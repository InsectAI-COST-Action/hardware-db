from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
# from datetime import datetime
import json
import copy

FORM_ID = "1k7RsEdOJrLW6ZDwOTHNdgDH2VSYWETfCI-1HyznB0m8" # full form

creds = Credentials.from_authorized_user_file(
    "token.json",
    scopes=["https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/drive",
            ]
)

forms_service = build("forms", "v1", credentials=creds)
# drive_service = build("drive", "v3", credentials=creds)

form = forms_service.forms().get(formId=FORM_ID).execute()

json.dump(form, open("extractedForm_temp.json", "w"), indent=4)

