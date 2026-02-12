#!/usr/bin/env python3
"""
Google Drive auth + simple file ops.

Works with:
  • OAUTH_CLIENT_JSON = path to a JSON file   (local .secrets or env var)
  • OAUTH_CLIENT_JSON = raw JSON string       (GitHub Actions secret)
"""

import os
import io
import json
import tempfile
from datetime import datetime

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ----------------------------------------------------------------------
# Helper: Turn the secret (path **or** raw JSON) into a real file path
# ----------------------------------------------------------------------
def _write_json_to_tmp(json_text: str) -> str:
    """Write a JSON string to a temporary file and return the file path."""
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="oauth_client_")
    os.close(fd)                     # close low‑level descriptor
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    return tmp_path


def resolve_oauth_path() -> str:
    """
    Return a filesystem path that points to a valid OAuth client JSON file.

    Preference order:
      1️⃣  OAUTH_CLIENT_JSON env var that already points to an existing file.
      2️⃣  OAUTH_CLIENT_JSON env var that contains the raw JSON payload.
      3️⃣  .secrets file with a line like:
          OAUTH_CLIENT_JSON=/full/path/to/client.json
    Raises:
      FileNotFoundError if nothing usable is found.
    """
    # ----- 1️⃣ Existing file? -----
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

    # ----- 2️⃣ .secrets fallback (local dev) -----
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
# Configuration
# ----------------------------------------------------------------------
OAUTH_CLIENT_JSON = resolve_oauth_path()          # <-- resolved path
TOKEN_FILE = os.getenv("TOKEN_TESTAUTH", "token_testAuth.json")
PARENT_DIR = "1UBiv4UnuLzDrOJbOgcRzgwqN2Y4Gv75S"   # hardware‑db Forms folder
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# ----------------------------------------------------------------------
# Authentication flow
# ----------------------------------------------------------------------
creds = None
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, SCOPES)
    creds = flow.run_local_server(port=0)

    # Persist the refreshed token for later runs
    with open(TOKEN_FILE, "w", encoding="utf-8") as token:
        token.write(creds.to_json())

drive_service = build("drive", "v3", credentials=creds)

# ----------------------------------------------------------------------
# File operations (create → rename → move → delete)
# ----------------------------------------------------------------------
file_content = "Hello world!"
media = MediaIoBaseUpload(
    io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain"
)

# 1️⃣ Create the file
created = (
    drive_service.files()
    .create(body={"name": "test.txt"}, media_body=media, fields="id")
    .execute()
)
file_id = created["id"]
print(f"✅ Created test file – ID: {file_id}")

# 2️⃣ Rename the file
drive_service.files().update(
    fileId=file_id,
    body={"name": f"Test File - {datetime.now():%Y-%m-%d_%H:%M:%S}"},
).execute()
print("🔄 Renamed file")

# 3️⃣ Retrieve current parents (need the ID field here)
metadata = (
    drive_service.files()
    .get(fileId=file_id, fields="id,parents")
    .execute()
)
previous_parents = ",".join(metadata.get("parents", []))

# 4️⃣ Move the file into the target folder
drive_service.files().update(
    fileId=file_id,
    addParents=PARENT_DIR,
    removeParents=previous_parents,
    fields="id,parents",
).execute()
print(f"📂 Moved file to folder {PARENT_DIR}")

# 5️⃣ Clean‑up (optional)
drive_service.files().delete(fileId=file_id).execute()
print("🗑️ Deleted test file – cleanup complete")