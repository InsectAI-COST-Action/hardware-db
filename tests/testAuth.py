import os
import io
# import json
# import tempfile
from datetime import datetime

# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config

### CONFIG
SCOPES = []
PARENT_DIR = ""
OAUTH_CLIENT_JSON = ""
TOKEN_TEST_AUTH = ""

### Get config values
cfg = build_config(globals())

oauth_path = resolve_oauth_path(cfg["OAUTH_CLIENT_JSON"])

### Make credentials
creds = None
creds = make_creds(oauth_path, cfg["TOKEN_TEST_AUTH"], cfg["SCOPES"])

### Create service with stored credentials
drive_service = build("drive", "v3", credentials=creds)


### Test authentication flow & permissions
# File operations (create → rename → move → delete)
file_content = "Hello world!"
media = MediaIoBaseUpload(
    io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain"
)

# Create the file
created = (
    drive_service.files()
    .create(body={"name": "test.txt"}, media_body=media, fields="id")
    .execute()
)
file_id = created["id"]
print(f"📃 Created test file – ID: {file_id}")

# Rename the file
drive_service.files().update(
    fileId=file_id,
    body={"name": f"Test File - {datetime.now():%Y-%m-%d_%H:%M:%S}"},
).execute()
print("🔄 Renamed file")

# Retrieve current parents (need the ID field here)
metadata = (
    drive_service.files()
    .get(fileId=file_id, fields="id,parents")
    .execute()
)
previous_parents = ",".join(metadata.get("parents", []))

# Move the file into the target folder
drive_service.files().update(
    fileId=file_id,
    addParents=cfg["PARENT_DIR"],
    removeParents=previous_parents,
    fields="id,parents",
).execute()
print(f"📂 Moved file to folder {cfg["PARENT_DIR"]}")

# Clean‑up (optional)
drive_service.files().delete(fileId=file_id).execute()
print("🗑️ Deleted test file – cleanup complete")