import os
import io
import json
import tempfile

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build

# ----------------------------------------------------------------------
# Helper: Turn the secret (path **or** raw JSON) into a real file path
# ----------------------------------------------------------------------
def _write_json_to_tmp(json_text: str) -> str:
    """Write a JSON string to a temporary file and return the file path."""
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="oauth_client_")
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    return tmp_path


def resolve_oauth_path() -> str:
    """
    Return a filesystem path that points to a valid OAuth client JSON file.

    Preference order:
      - OAUTH_CLIENT_JSON env var that already points to an existing file.
      - OAUTH_CLIENT_JSON env var that contains the raw JSON payload.
      - .secrets file with a line like: OAUTH_CLIENT_JSON=/full/path/to/client.json
    Raises:
      FileNotFoundError if nothing usable is found.
    """
    # ----- Existing file? -----
    env_val = os.getenv("OAUTH_CLIENT_JSON")
    if env_val:
        if os.path.isfile(env_val):
            # It's already a path – use it directly.
            return env_val

        # Not a file → assume it is the raw JSON text.
        try:
            json.loads(env_val)          # sanity‑check that it parses
        except Exception as exc:
            raise FileNotFoundError(
                "OAUTH_CLIENT_JSON is set but is neither a valid file nor valid JSON."
            ) from exc
        # Write the JSON to a temp file and hand that path back.
        return _write_json_to_tmp(env_val)

    # ----- .secrets fallback (local dev) -----
    secrets_file = ".secrets"
    if os.path.isfile(secrets_file):
        with open(secrets_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("OAUTH_CLIENT_JSON="):
                    candidate = line.split("=", 1)[1].strip()
                    if os.path.isfile(candidate):
                        return candidate
                    raise FileNotFoundError(
                        f"The path '{candidate}' referenced in .secrets does not exist."
                    )

    # ----- Nothing worked -----
    raise FileNotFoundError(
        "Unable to locate OAuth client JSON. Either set the OAUTH_CLIENT_JSON "
        "environment variable (to a path or to the raw JSON) or create a "
        ".secrets file containing a line like:\n"
        "OAUTH_CLIENT_JSON=/full/path/to/OAuth_client.json"
    )

# ----------------------------------------------------------------------
# Helper: Load OAuth tokens and return creds object, supports:
#   * Fresh token via local server (when you run the script locally)
#   * Re‑using a stored refresh token (CI/CD)
# ----------------------------------------------------------------------
def make_creds(OAUTH_CLIENT_JSON, TOKEN_FILE, SCOPES):
    # Try to load a persisted token file (useful when you run locally)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

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

        # Persist the fresh token for the next local run
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
            
    return creds
