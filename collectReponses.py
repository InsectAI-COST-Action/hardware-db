from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = [
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]

OAUTH_CLIENT_JSON = "D:\\hardware-db\\OAuth_client-WSL_laptop.json"
TOKEN_FILE = "token_collectResponses.json"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
FORM_ID = "1hg7KuM9BkXK8quQqQXAh4CXQrpT-JazrjKLzKQNgYw8"


# Authenticatation flow
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

# creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes=SCOPES)
# forms_service = build("forms", "v1", credentials=creds)
# # drive_service = build("drive", "v3", credentials=creds)

forms_service = build(
    "forms",
    "v1",
    credentials=creds,
    discoveryServiceUrl=DISCOVERY_DOC,
    static_discovery=False,
)

# Prints the title of the sample form:
form_id = FORM_ID
result = forms_service.forms().get(formId=form_id).execute()
print(result)

# Prints all results from the form:
result = forms_service.forms().responses().list(formId=form_id).execute()
print(result)