# src/configParsing.py
import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Callable

# ----------------------------------------------------------------------
# Load a simple “KEY=VALUE” file (ignore blanks & lines that start with #)
# ----------------------------------------------------------------------
def load_secrets(path: Path) -> Dict[str, str]:
    """Read a .secrets‑style file into a dict of raw strings."""
    secrets: Dict[str, str] = {}
    if not path.is_file():
        return secrets
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            secrets[k.strip()] = v.strip()
    return secrets


# ----------------------------------------------------------------------
# Convert a raw string to the type we expect for a particular key.
# The expected type is derived from the caller's globals (see _type_for_key).
# ----------------------------------------------------------------------
def _coerce_value(raw: str, target_type: Callable[[str], Any]) -> Any:
    """
    Convert *raw* (always a string) into *target_type*.
    Supported target_type callables are:
        - str   : identity
        - bool  : "true"/"1"/"yes"/"on" → True, everything else → False
        - list  : space‑separated tokens → List[str]
    """
    if target_type is str:
        return raw

    if target_type is bool:
        return raw.lower() in {"1", "true", "yes", "on"}

    if target_type is list:
        # split on whitespace, ignore empty entries
        return [tok for tok in raw.split() if tok]

    # Fallback – try to call the type directly (e.g. int, float)
    try:
        return target_type(raw)
    except Exception as exc:
        raise ValueError(f"Cannot coerce value '{raw}' to {target_type}") from exc


def _type_for_key(key: str, caller_globals: Dict[str, Any]) -> Callable[[str], Any]:
    """
    Inspect the caller's globals to decide what Python type a key should have.
    Conventions:
        * Upper‑case constants that are **lists** (e.g. SCOPES) → list
        * Upper‑case constants that are **bools** (e.g. DEBUG) → bool
        * Everything else → str
    """
    # If the caller defined a default value, we can infer the type from it.
    default_val = caller_globals.get(key)
    if isinstance(default_val, bool):
        return bool
    if isinstance(default_val, list):
        return list
    # No explicit default – fall back to heuristics based on the key name.
    if key == "DEBUG":
        return bool
    if key == "SCOPES":
        return list
    return str


# ----------------------------------------------------------------------
# Choose the final value for a single key according to the required order:
#   1 CLI argument (non‑None)
#   2 .secrets entry (string → coerced)
#   3 Environment variable (string → coerced)
# If none of the three sources provide a value we raise an error.
# ----------------------------------------------------------------------
def pick_cfg_value(
    key: str,
    cli_val: Any,
    secret_dict: Dict[str, str],
    caller_globals: Dict[str, Any],
) -> Any:
    """
    Returns the configuration value for *key* after applying precedence and
    type coercion.  Raises ``ValueError`` if the key cannot be satisfied.
    
    Precedence is:
        1. CLI argument (if not None)
        2. .secrets file entry (if present)
        3. Environment variable (if present)
        4. Defaults for some keys
        5. Otherwise, error.
    """
    # 1️⃣ CLI argument – already the correct Python type because argparse does it.
    if cli_val is not None:
        return cli_val

    # Determine the target type once (used for both .secrets and env).
    target_type = _type_for_key(key, caller_globals)

    # 2️⃣ .secrets file – always a raw string, so we coerce.
    if key in secret_dict:
        return _coerce_value(secret_dict[key], target_type)

    # 3️⃣ Environment variable – also a raw string.
    env_raw = os.getenv(key)
    if env_raw is not None:
        return _coerce_value(env_raw, target_type)

    # Nothing found → explicit failure.
    raise ValueError(
        f"Configuration value for '{key}' not supplied. Provide it via CLI, a .secrets "
        f"file, or an environment variable."
    )


# ----------------------------------------------------------------------
# Build the full configuration dict for *any* script.
# The caller passes its ``globals()`` so we know which keys it expects.
# ----------------------------------------------------------------------
def build_config(caller_globals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses CLI arguments, loads an optional .secrets file, checks environment
    variables, coerces values to the expected Python types, and returns a dict.
    Missing required keys raise ``ValueError``.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Collect Google Form responses (or any other script) "
            "with overridable configuration."
        )
    )
    # ------------------------------------------------------------------
    # Shared CLI options – defaults for some only
    # ------------------------------------------------------------------
    parser.add_argument(
        "--scopes",
        nargs="+",
        help="OAuth scopes (space‑separated).",
    )
    parser.add_argument(
        "--schema-file",
        # default="hardware-db_schema.json",
        help="Path to the form schema JSON file.",
    )
    parser.add_argument("--form-id", help="Google Form ID.")
    parser.add_argument(
        "--oauth-client-json",
        help="Path or raw JSON for OAuth client credentials.",
    )
    parser.add_argument(
        "--token-collect-responses",
        help="Token cache file for collectResponses.py.",
    )
    parser.add_argument(
        "--token-create-form",
        help="Token cache file for createForm.py.",
    )
    parser.add_argument(
        "--discovery-doc",
        help="Forms API discovery doc URL.",
    )
    parser.add_argument(
        "--debug",
        action="store_false",
        help="Enable verbose debug output.",
    )
    parser.add_argument(
        "--parent-dir",
        help="Drive folder ID that will hold the created form.",
    )
    parser.add_argument(
        "--secrets-file",
        default=".secrets",
        help="Path to a .secrets file (default: .secrets).",
    )

    # ------------------------------------------------------------------
    # Parse CLI – this will automatically exit with a nice help message
    # if the user supplies `-h/--help`.
    # ------------------------------------------------------------------
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load .secrets (if it exists)
    # ------------------------------------------------------------------
    secret_vals = load_secrets(Path(args.secrets_file))

    # ------------------------------------------------------------------
    # Determine which upper‑case names the caller cares about.
    # By convention we treat every UPPERCASE global as a required config key.
    # ------------------------------------------------------------------
    expected_keys = [
        name for name, val in caller_globals.items() if name.isupper()
    ]

    # ------------------------------------------------------------------
    # Assemble the final configuration dict, applying precedence and
    # type‑coercion for each key.
    # ------------------------------------------------------------------
    cfg: Dict[str, Any] = {}
    for key in expected_keys:
        # CLI attributes are the lower‑case version of the constant name.
        cli_attr = key.lower()
        cli_val = getattr(args, cli_attr, None)

        cfg[key] = pick_cfg_value(
            key,
            cli_val,
            secret_vals,
            caller_globals,
        )

    return cfg