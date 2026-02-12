from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import io, os
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

OAUTH_CLIENT_JSON = "D:\\hardware-db\\OAuth_client-WSL_laptop.json"
TOKEN_FILE = "token_testAuth.json"
PARENT_DIR = "1UBiv4UnuLzDrOJbOgcRzgwqN2Y4Gv75S" # hardware-db Forms folder

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
