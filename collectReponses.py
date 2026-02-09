from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

import json
import csv
import re
from pathlib import Path


SCOPES = [
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]

OAUTH_CLIENT_JSON = "D:\\hardware-db\\OAuth_client-WSL_laptop.json"
TOKEN_FILE = "token_collectResponses.json"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
FORM_ID = "1hg7KuM9BkXK8quQqQXAh4CXQrpT-JazrjKLzKQNgYw8"


### Authenticatation flow
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


### Grab form details - we need this for the questionId's
form_info = forms_service.forms().get(formId=FORM_ID).execute()
# print(form_info)

form_info = form_info.get("items")
# print(form_info)

# Make dictionary of question IDs (idQ) to question titles (titleQ)
idQ_to_titleQ = {}
for item in form_info:
    # print(item)
    if "questionItem" in item:
        idQ_to_titleQ[item["questionItem"]["question"]["questionId"]] = item["title"]

print(idQ_to_titleQ)


### grab JSON schema, parse into handy dictionary - we need to match questionId to question title
with open("hardware-db_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# shortQ -> shorthand for question
# titleQ -> actual question text
shortQ_to_titleQ = {}
ordered_shortQ_to_titleQ = []

for section in schema["sections"]:
    for q in section["questions"]:
        qid = q["id"]
        title = q["title"]
        shortQ_to_titleQ[qid] = title
        ordered_shortQ_to_titleQ.append(qid)


### Grab the responses - this contains the answers proper
responses = forms_service.forms().responses().list(formId=FORM_ID).execute()
# print(responses)

responses = responses.get("responses", [])
print(f"Found {len(responses)} responses")

