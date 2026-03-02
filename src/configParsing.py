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
        * Everything else → str (especially for keys from external files)
    
    If the key is not declared in the script, defaults to str.
    """
    # If the caller defined a default value, we can infer the type from it.
    default_val = caller_globals.get(key)
    if isinstance(default_val, bool):
        return bool
    if isinstance(default_val, list):
        return list
    
    # No explicit default – fall back to key-name heuristics
    if key == "DEBUG":
        return bool
    if key == "SCOPES":
        return list
    
    # Default for everything else (including external .env/.secrets keys)
    return str


# ----------------------------------------------------------------------
# Choose the final value for a single key according to the required order:
#   1 CLI argument (non‑None)
#   2 Environment variable (string → coerced)
#   3 .secrets entry (string → coerced)
#   4 Defaults for some keys
# If none of the three sources provide a value we raise an error.
# ----------------------------------------------------------------------
def pick_cfg_value(
    key: str,
    cli_val: Any,
    hardcoded_val: Any,
    file_dict: Dict[str, str],
    caller_globals: Dict[str, Any],
    is_declared: bool = False,
) -> Any:
    """
    Returns the configuration value for *key* after applying precedence and
    type coercion. Only raises ValueError if the key is declared in the script
    and cannot be satisfied from any source.
    
    Precedence (highest to lowest):
        1. CLI argument (if not None)
        2. Hardcoded value in script (if not None/empty)
        3. .env or .secrets file entry (if present)
        4. Otherwise: error if declared, None if not declared
    
    Parameters
    ----------
    key : str
        The configuration key name
    cli_val : Any
        Value from CLI argument (already typed by argparse)
    hardcoded_val : Any
        Value from the caller's globals (hardcoded in script)
    file_dict : Dict[str, str]
        Combined dict of .env and .secrets values (all strings)
    caller_globals : Dict[str, Any]
        The caller's globals (for type inference)
    is_declared : bool
        Whether this key is a declared UPPERCASE variable in the script.
        If True and value cannot be satisfied, raise error.
    """
    # 1. CLI argument – already the correct Python type because argparse does it.
    if cli_val is not None:
        return cli_val

    # 2. Hardcoded value in script – use as-is (already correct type)
    if hardcoded_val is not None and hardcoded_val != "":
        return hardcoded_val

    # Determine the target type for file values
    target_type = _type_for_key(key, caller_globals)

    # 3. Value from .env/.secrets file – always a raw string, so we coerce
    if key in file_dict:
        return _coerce_value(file_dict[key], target_type)
    
    # Nothing found
    if is_declared:
        # Declared variables are required
        raise ValueError(
            f"Configuration value for '{key}' not supplied. Provide it via CLI, "
            f"hardcode it in the script, or add it to .env or .secrets."
        )
    else:
        # Undeclared variables are optional (e.g., from external .env files)
        return None


# ----------------------------------------------------------------------
# Build the full configuration dict for *any* script.
# The caller passes its ``globals()`` so we know which keys it declares.
# All keys from .env and .secrets are also included automatically.
# ----------------------------------------------------------------------
def build_config(caller_globals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses CLI arguments, loads .env and .secrets files, applies precedence
    to configuration values, and returns a complete config dict.
    
    Behavior:
    * Scripts do NOT need to declare all variables
    * All values from .env and .secrets are automatically included
    * Declared variables (UPPERCASE in caller_globals) are required
    * Undeclared variables from external files are optional (always included if present)
    
    Precedence for each key:
        1. CLI arguments (highest priority)
        2. Hardcoded values in the calling script
        3. Values from .env or .secrets files
        4. Error if declared but not found; None if undeclared and not found
    """
    parser = argparse.ArgumentParser(
        description=(
            "Configuration management supporting CLI, hardcoded defaults, "
            "and external .env/.secrets files."
        )
    )
    # ------------------------------------------------------------------
    # Shared CLI options
    # ------------------------------------------------------------------
    parser.add_argument(
        "--scopes",
        nargs="+",
        help="OAuth scopes (space‑separated).",
    )
    parser.add_argument(
        "--schema-file",
        help="Path to the form schema JSON file.",
    )
    parser.add_argument(
        "--form-id", 
        help="Google Form ID."
    )
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
        "--token-test-auth",
        help="Token cache file for testAuth.py.",
    )
    parser.add_argument(
        "--token-form-trigger",
        help="Token cache file for formTrigger scripts.",
    )
    parser.add_argument(
        "--discovery-doc",
        help="Forms API discovery doc URL.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug output.",
    )
    parser.add_argument(
        "--parent-dir",
        help="Drive folder ID that will hold the created form.",
    )
    parser.add_argument(
        "--update-links",
        action="store_true",
        help="Update form ID and links in README (default: False).",
    )
    parser.add_argument(
        "--secrets-file",
        default=".secrets",
        help="Path to a .secrets file (default: .secrets).",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file (default: .env).",
    )

    # ------------------------------------------------------------------
    # Parse CLI
    # ------------------------------------------------------------------
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load .env and .secrets
    # ------------------------------------------------------------------
    env_vals = load_secrets(Path(args.env_file))
    secret_vals = load_secrets(Path(args.secrets_file))
    
    # Merge with .secrets taking precedence over .env
    all_file_config = {**env_vals, **secret_vals}

    # ------------------------------------------------------------------
    # Determine which keys are declared in the script
    # ------------------------------------------------------------------
    declared_keys = [
        name for name, val in caller_globals.items() if name.isupper()
    ]

    # ------------------------------------------------------------------
    # Collect all keys: declared keys + all keys from .env/.secrets
    # ------------------------------------------------------------------
    all_keys = set(declared_keys) | set(all_file_config.keys())

    # ------------------------------------------------------------------
    # Process all keys with proper precedence
    # ------------------------------------------------------------------
    cfg: Dict[str, Any] = {}
    
    for key in all_keys:
        # Get the value from each source (or None if not present)
        cli_attr = key.lower()
        cli_val = getattr(args, cli_attr, None)
        hardcoded_val = caller_globals.get(key)
        is_declared = key in declared_keys

        # Apply precedence and type coercion
        value = pick_cfg_value(
            key,
            cli_val,
            hardcoded_val,
            all_file_config,
            caller_globals,
            is_declared=is_declared,
        )
        
        # Only add to cfg if we got a value (declared keys always get a value or raise)
        if value is not None:
            cfg[key] = value

    return cfg