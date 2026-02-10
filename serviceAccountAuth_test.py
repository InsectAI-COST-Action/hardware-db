import os
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

# Build Forms API service
forms_service = build("forms", "v1", credentials=credentials)

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
