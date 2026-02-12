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
# Helper: Resolve the OAuth client JSON location / content
# ----------------------------------------------------------------------
def _write_secret_to_tempfile(secret_json: str) -> str:
    """Write the raw JSON string to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="oauth_client_")
    # Close the low‑level descriptor, then write with normal Python I/O
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(secret_json)
    return path


def resolve_oauth_path() -> str:
    """
    Return a filesystem path that points to a valid OAuth client JSON file.

    Preference order:
      1️⃣  OAUTH_CLIENT_JSON env var containing a **path** (GitHub Actions case when you
          deliberately write the secret to a file beforehand).
      2️⃣  OAUTH_CLIENT_JSON env var containing **raw JSON** – we dump it to a temp file.
      3️⃣  .secrets file in the current working directory with a line like:
          OAUTH_CLIENT_JSON=/full/path/to/client.json
    Raises:
      FileNotFoundError if nothing usable is found.
    """
    # 1️⃣  Env var already points to an existing file?
    env_val = os.getenv("OAUTH_CLIENT_JSON")
    if env_val:
        # If the value is a path that actually exists, use it directly.
        if os.path.isfile(env_val):
            return env_val

        # Otherwise we assume the env var holds the raw JSON payload.
        try:
            # Quick sanity‑check: it should be parseable JSON.
            json.loads(env_val)
        except Exception as exc:
            raise FileNotFoundError(
                "OAUTH_CLIENT_JSON is set but does not point to a file "
                "and is not valid JSON."
            ) from exc

        # Write the JSON to a temporary file and hand that path back.
        return _write_secret_to_tempfile(env_val)

    # 2️⃣  Look for a .secrets file (local development)
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
                    else:
                        raise FileNotFoundError(
                            f"The path '{candidate}' referenced in .secrets does not exist."
                        )

    # Nothing worked – give a helpful error.
    raise FileNotFoundError(
        "Unable to locate OAuth client JSON. Either set the OAUTH_CLIENT_JSON "
        "environment variable (to a path or to the raw JSON) or create a "
        ".secrets file containing a line like:\n"
        "OAUTH_CLIENT_JSON=/full/path/to/OAuth_client.json"
    )


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OAUTH_CLIENT_JSON = resolve_oauth_path()
TOKEN_FILE = os.getenv("TOKEN_TESTAUTH", "token_testAuth.json")
PARENT_DIR = "1UBiv4UnuLzDrOJbOgcRzgwqN2Y4Gv75S"   # hardware‑db Forms folder
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


#### Authentication flow
creds = None

if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(
        OAUTH_CLIENT_JSON, SCOPES
    )
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())


drive_service = build("drive", "v3", credentials=creds)

file_content = "Hello world!"
media = MediaIoBaseUpload(io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain")


### Create text file for testing
file = drive_service.files().create(
    body={"name": "test.txt"},
    media_body=media,
    fields="id"
).execute()

print("Created test file")


### Rename and move file to specified folder
drive_service.files().update(
    fileId=file["id"],
    body={
        "name": "Test File - "
                f"{datetime.today().strftime('%Y-%m-%d_%H:%M:%S')}"
    }
).execute()

# Get current parents
file = drive_service.files().get(
    fileId=file["id"],
    fields="id, parents"
).execute()

previous_parents = ",".join(file.get("parents"))

# Move the file
drive_service.files().update(
    fileId=file["id"],
    addParents=PARENT_DIR,
    removeParents=previous_parents,
    fields="id, parents"
).execute()

print("File renamed and moved successfully")


### Delete test file
drive_service.files().delete(fileId=file["id"]).execute()

print("Cleaning up: deleted test file")
