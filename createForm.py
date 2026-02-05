from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import json


DB_VERSION = "v0.1"

creds = Credentials.from_authorized_user_file(
    "token.json",
    scopes=["https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/drive",
            ]
)

forms_service = build("forms", "v1", credentials=creds)
drive_service = build("drive", "v3", credentials=creds)

### Create form
form = forms_service.forms().create(
    body={"info": {"title": "Multi-section test form from API"}}
).execute()

form_id = form["formId"]
# form_id = "1b3EvmixvLWugaq8wnKANgeGrWxMC6Dr5V65KkSWbgig" # override ID for testing

### Using batch updates to input questions into form
with open("formMultisectionTest.json", "r") as f:
    requests = json.load(f)

forms_service.forms().batchUpdate(
    formId=form_id,
    body={"requests": requests}
).execute()

### Rename the form in Drive
drive_service.files().update(
    fileId=form_id,
    body={
        "name": "f{datetime.today().strftime('%Y-%m-%dT%H:%M:%S')} - InsectAI hardware database submission form, f{DB_VERSION}"
    }
).execute()
