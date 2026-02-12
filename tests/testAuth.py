from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime

OAUTH_CLIENT_JSON = "D:\\hardware-db\\OAuth_client-WSL_laptop.json"
PARENT_DIR = "1UBiv4UnuLzDrOJbOgcRzgwqN2Y4Gv75S" # hardware-db Forms folder

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file(
    OAUTH_CLIENT_JSON, SCOPES
)
creds = flow.run_local_server(port=0)

drive_service = build("drive", "v3", credentials=creds)

file_content = "Hello world!"
media = MediaIoBaseUpload(io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain")


### Create text file for testing
file = drive_service.files().create(
    body={"name": "test.txt"},
    media_body=media,
    fields="id"
).execute()

print("Created file ID:", file["id"])


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

# Move the form
drive_service.files().update(
    fileId=file["id"],
    addParents=PARENT_DIR,
    removeParents=previous_parents,
    fields="id, parents"
).execute()

print("File renamed and moved successfully:")
print(f"https://docs.google.com/forms/d/{file["id"]}/edit")