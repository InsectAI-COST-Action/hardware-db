# src/configParsing.py
import argparse
import os
from pathlib import Path
from typing import Any, Dict, List
import inspect


# ----------------------------------------------------------------------
# Load a simple “KEY=VALUE” file (ignore blanks & lines that start with #)
# ----------------------------------------------------------------------
def load_secrets(path: Path) -> Dict[str, str]:
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
# Pick the final value for a single key
# ----------------------------------------------------------------------
def choose_cfg_value(
    key: str,
    cli_val: Any,
    secret_dict: Dict[str, str],
    default: Any,
) -> Any:
    """
    Precedence order:
        1. CLI argument (non‑None)
        2. `.secrets` entry (always a string → cast to the type of *default*)
        3. The hard‑coded default that lives in the caller module.
    """
    if cli_val is not None:
        return cli_val

    if key in secret_dict:
        # Secrets are strings – coerce to the type of the default.
        if isinstance(default, bool):
            return secret_dict[key].lower() in {"1", "true", "yes", "on"}
        if isinstance(default, list):
            # Assume space‑separated list in the .secrets file.
            return secret_dict[key].split()
        # For int/float you could add extra branches here.
        return secret_dict[key]

    return default


# ----------------------------------------------------------------------
# Build the full configuration dict for *any* script
# ----------------------------------------------------------------------
def build_config(caller_module) -> Dict[str, Any]:
    """
    `caller_module` is typically `globals()` from the script that calls us.
    The function:
        • defines the CLI arguments that every script shares,
        • reads the optional .secrets file,
        • pulls the defaults from the caller’s globals(),
        • returns a dict with the final values.
    """
    parser = argparse.ArgumentParser(
        description="Collect Google Form responses (or any other script) "
        "with overridable configuration."
    )
    parser.add_argument(
        "--scopes",
        nargs="+",
        help="OAuth scopes (space‑separated).",
    )
    parser.add_argument(
        "--schema-file",
        default="hardware-db_schema.json",
        help="Path to the form schema JSON file (default: hardware-db_schema.json).",
    )
    parser.add_argument("--form-id", help="Google Form ID.")
    parser.add_argument(
        "--oauth-client-json",
        help="Path or raw JSON for OAuth client credentials.",
    )
    parser.add_argument("--token-file", help="Token cache file.")
    parser.add_argument("--discovery-doc", help="Forms API discovery doc URL.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug output.",
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
    # Helper to fetch a default from the caller’s globals().
    # If the caller didn’t define the name, we fall back to `None`
    # (the choose_cfg_value function will then simply return the CLI or secret value).
    # ------------------------------------------------------------------
    def _default(name: str) -> Any:
        return caller_module.get(name, None)

    # ------------------------------------------------------------------
    # Assemble the final configuration dict.
    # Each entry uses the same precedence logic.
    # ------------------------------------------------------------------
    cfg = {
        "SCOPES": choose_cfg_value("SCOPES", args.scopes, secret_vals, _default("SCOPES")),
        "SCHEMA_FILE": choose_cfg_value("SCHEMA_FILE", args.schema_file, secret_vals, _default("SCHEMA_FILE")),
        "FORM_ID": choose_cfg_value("FORM_ID", args.form_id, secret_vals, _default("FORM_ID")),
        "OAUTH_CLIENT_JSON": choose_cfg_value(
            "OAUTH_CLIENT_JSON", args.oauth_client_json, secret_vals, _default("OAUTH_CLIENT_JSON")
        ),
        "TOKEN_FILE": choose_cfg_value("TOKEN_FILE", args.token_file, secret_vals, _default("TOKEN_FILE")),
        "DISCOVERY_DOC": choose_cfg_value(
            "DISCOVERY_DOC", args.discovery_doc, secret_vals, _default("DISCOVERY_DOC")
        ),
        "DEBUG": choose_cfg_value("DEBUG", args.debug, secret_vals, _default("DEBUG")),
    }

    return cfg