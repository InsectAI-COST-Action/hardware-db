import argparse
import os
from pathlib import Path
from typing import Any, Dict, List


"""
Priority: CLI > .secrets > defaults

Argparse support:
    * All top‑level configuration constants can be overridden via CLI.
    * A .secrets file (key=value per line) is also read.
    * Command‑line arguments always win.
"""

def load_secrets(path: Path) -> Dict[str, str]:
    """Parse a simple KEY=VALUE file (ignore blanks & comments)."""
    secrets = {}
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


def choose_cfg_value(key: str, cli_val: Any, secret_dict: Dict[str, str], default: Any) -> Any:
    """
    Return the value that should be used for *key*.
    Precedence: CLI argument > .secrets entry > hard‑coded default.
    """
    if cli_val is not None:
        return cli_val
    if key in secret_dict:
        # Secrets are always strings – try to cast to the type of the default
        if isinstance(default, bool):
            return secret_dict[key].lower() in {"1", "true", "yes", "on"}
        if isinstance(default, list):
            # Assume space‑separated list in the .secrets file
            return secret_dict[key].split()
        return secret_dict[key]
    return default


def _build_config() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Collect Google Form responses and export them."
    )
    parser.add_argument(
        "--scopes",
        nargs="+",
        help="OAuth scopes (space‑separated).",
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

    args = parser.parse_args()

    # Load .secrets (if it exists)
    secret_vals = load_secrets(Path(args.secrets_file))

    cfg = {
        "SCOPES": choose_cfg_value(
            "SCOPES", args.scopes, secret_vals, SCOPES
        ),
        "FORM_ID": choose_cfg_value(
            "FORM_ID", args.form_id, secret_vals, FORM_ID
        ),
        "SCHEMA_FILE": choose_cfg_value(
            "SCHEMA_FILE", args.schema_file, secret_vals, SCHEMA_FILE
        ),
        "PARENT_DIR": choose_cfg_value(
            "PARENT_DIR", args.parent_dir, secret_vals, PARENT_DIR
        ),
        "OAUTH_CLIENT_JSON": choose_cfg_value(
            "OAUTH_CLIENT_JSON", args.oauth_client_json, secret_vals, OAUTH_CLIENT_JSON
        ),
        "TOKEN_FILE": choose_cfg_value(
            "TOKEN_FILE", args.token_file, secret_vals, TOKEN_FILE
        ),
        "DISCOVERY_DOC": choose_cfg_value(
            "DISCOVERY_DOC", args.discovery_doc, secret_vals, DISCOVERY_DOC
        ),
        "DEBUG": choose_cfg_value("DEBUG", args.debug, secret_vals, DEBUG
        ),
    }

    return cfg
