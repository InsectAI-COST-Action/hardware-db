import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Union

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# ----------------------------------------------------------------------
# Helper: Turn the secret (path **or** raw JSON) into a real file path
# ----------------------------------------------------------------------
def _is_json_string(s: str) -> bool:
    """
    Valid JSON check: True if the stripped string starts with `{` and ends with `}`.
    """
    s = s.strip()
    return s.startswith("{") and s.endswith("}")


def resolve_oauth_path(value: Optional[Union[str, Path]]) -> Path:
    """
    Turn *any* representation of the OAuth client credentials into a concrete
    filesystem Path that the Google libraries can consume.
    
    It support, in order of priority:
    1. An explicit file path that already exists.
    2. A raw JSON string (the full OAuth client JSON).
    3. ``None`` – in which case we raise a clear error telling the caller
       to supply the variable via CLI, .secrets, or the environment.
    
    Parameters
    ----------
    value:
        The value obtained from the configuration layer.  It may be:
        * ``Path`` or ``str`` pointing at a file,
        * a raw JSON string,
        * ``None``.

    Returns
    -------
    pathlib.Path
        Path to a real file containing the OAuth client definition.

    Raises
    ------
    FileNotFoundError
        If ``value`` is ``None`` or points at a non‑existent file.
    ValueError
        If ``value`` looks like JSON but cannot be parsed (protects against
        accidental malformed strings).
    """
    
    ### No value at all → Error, caller must provide something
    if value is None:
        raise FileNotFoundError(
            "OAUTH_CLIENT_JSON not supplied. Provide it via a CLI argument, "
            "a .secrets file, or an environment variable."
        )
    # Normalise to a string for the checks below
    candidate = str(value).strip()

    ### Existing file on disk?
    path_candidate = Path(candidate).expanduser().resolve()
    if path_candidate.is_file():
        return path_candidate

    ### Raw JSON string? (starts with { and ends with })
    if _is_json_string(candidate):
        try:
            # Validate that it is real JSON – this catches obvious typos.
            json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Provided OAUTH_CLIENT_JSON looks like JSON but is malformed."
            ) from exc

        # Write the JSON to a temporary file that will live for the process.
        tmp_dir = Path(tempfile.gettempdir())
        tmp_file = tmp_dir / f"oauth_client_{os.getpid()}.json"
        tmp_file.write_text(candidate, encoding="utf-8")
        return tmp_file

    ### Anything else is an error – cannot guess what the user meant.
    raise FileNotFoundError(
        f"The value supplied for OAUTH_CLIENT_JSON ('{candidate}') is neither a "
        "readable file nor a raw JSON string. Supply a valid path or raw JSON."
    )

# ----------------------------------------------------------------------
# Helper: Load OAuth tokens and return creds object, supports:
#   * Fresh token via local server (when you run the script locally)
#   * Re‑using a stored refresh token (CI/CD)
# ----------------------------------------------------------------------
def make_creds(OAUTH_CLIENT_JSON, TOKEN_FILE, SCOPES):
    # Try to load a persisted token file (useful when you run locally)
    creds = None
    if TOKEN_FILE and isinstance(TOKEN_FILE, (str, Path)) and os.path.isfile(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as exc:          # e.g. malformed / stale file
            print(f"⚠️  Could not load token file '{TOKEN_FILE}': {exc}")
            creds = None

    # If we have a refresh‑token secret (CI), load it and build Credentials
    if not creds or not creds.valid:
        # Look for the REFRESH_TOKEN_JSON secret (exposed as env var)
        refresh_blob_raw = os.getenv("REFRESH_TOKEN_JSON")
        if refresh_blob_raw:
            try:
                refresh_blob = json.loads(refresh_blob_raw)
                creds = Credentials(
                    token=refresh_blob.get("token"),
                    refresh_token=refresh_blob.get("refresh_token"),
                    token_uri=refresh_blob.get("token_uri"),
                    client_id=refresh_blob.get("client_id"),
                    client_secret=refresh_blob.get("client_secret"),
                    scopes=refresh_blob.get("scopes"),
                )
                # Force a refresh if the access token is expired or missing
                if not creds.valid or creds.expired:
                    creds.refresh(Request())
            except Exception as exc:
                raise RuntimeError(
                    "Failed to parse REFRESH_TOKEN_JSON – ensure the secret contains the full JSON blob."
                ) from exc

    # If we still have no credentials, fall back to the interactive flow (local dev)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, SCOPES)
        creds = flow.run_local_server(port=0)   # opens a browser – only works locally

        # Persist the fresh token for the next local run (if TOKEN_FILE is valid)
        if TOKEN_FILE and isinstance(TOKEN_FILE, (str, Path)):
            token_path = Path(TOKEN_FILE)
            try:
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
                print(f"[+] Saved token to {token_path}")
            except Exception as exc:
                print(f"[!] Could not save token to '{TOKEN_FILE}': {exc}")
            
    return creds
