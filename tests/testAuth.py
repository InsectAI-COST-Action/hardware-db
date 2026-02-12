from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseUpload

OAUTH_CLIENT_JSON = "D:\\hardware-db\\OAuth_client-WSL_laptop.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file(
    OAUTH_CLIENT_JSON, SCOPES
)
creds = flow.run_local_server(port=0)

drive_service = build("drive", "v3", credentials=creds)

file_content = "Hello world!"
media = MediaIoBaseUpload(io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain")

file = drive_service.files().create(
    body={"name": "test.txt"},
    media_body=media,
    fields="id"
).execute()

print("Created file ID:", file["id"])
