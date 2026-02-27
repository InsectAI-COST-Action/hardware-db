import os, io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# -----------------------------
# Read secrets
# -----------------------------
with open(".secrets") as f:
    secrets = f.readlines()
    secrets = [line.rstrip('\n') for line in secrets]

secrets_dict = {}
for secret in secrets:
    # print(secret)
    split = secret.split("=")
    # print(split[0], split[1])
    secrets_dict[split[0]] = split[1]

GOOGLE_SERVICE_JSON_KEY = secrets_dict.get("GOOGLE_SERVICE_JSON_KEY")

if not GOOGLE_SERVICE_JSON_KEY:
    raise ValueError("GOOGLE_SERVICE_JSON_KEY not found in .secrets file")

# -----------------------------
# Required scopes
# -----------------------------
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive"
]

# -----------------------------
# Authenticate using service account
# -----------------------------
service_account_info = json.load(open(GOOGLE_SERVICE_JSON_KEY))
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)
forms_service = build("forms", "v1", credentials=credentials)


### Create Drive file first, then update
file_metadata = {
    "name": "Insect Monitoring Form",
    "mimeType": "application/vnd.google-apps.form",
    "parents": [secrets_dict.get("DRIVE_FORMS_FOLDER")]
}

import io
from googleapiclient.http import MediaIoBaseUpload
file_content = "Hello! This is the content of the text file."
media = MediaIoBaseUpload(io.BytesIO(file_content.encode("utf-8")), mimetype="text/plain")

file = drive_service.files().create(
    body={
        "name": "test.txt",
        "mimeType": "text/plain",
        "parents": [secrets_dict.get("DRIVE_FORMS_FOLDER")],
    },
    media_body=media,
    supportsAllDrives=True,
    fields="id, parents"
).execute() ### this now fails too

drive_service.files().create(
    body=file_metadata,
    supportsAllDrives=True,
    fields="id"
).execute()


# -----------------------------
# 1. Create a new form
# -----------------------------
NEW_FORM = {
    "info": {
        "title": "Insect Monitoring Test Form",
        "documentTitle": "Insect Monitoring Test Form"
    }
}

result = forms_service.forms().create(body=NEW_FORM).execute()
form_id = result["formId"]

print(f"Created form with ID: {form_id}")
print(f"Edit URL: {result['responderUri']}")

# -----------------------------
# 2. Use batchUpdate to add a question
# -----------------------------
requests = [
    {
        "createItem": {
            "item": {
                "title": "What insect did you observe?",
                "questionItem": {
                    "question": {
                        "required": True,
                        "choiceQuestion": {
                            "type": "RADIO",
                            "options": [
                                {"value": "Bee"},
                                {"value": "Butterfly"},
                                {"value": "Hoverfly"},
                                {"value": "Other"}
                            ]
                        }
                    }
                }
            },
            "location": {
                "index": 0
            }
        }
    }
]

batch_update_request = {
    "requests": requests
}

forms_service.forms().batchUpdate(
    formId=form_id,
    body=batch_update_request
).execute()

print("Successfully added question via batchUpdate.")
