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

####################

parsed_rows = []

for response in responses:
    answer_map = {}

    answers = response.get("answers", {})

    for question_id in idQ_to_titleQ.keys():

        if question_id in answers:
            answer_obj = answers[question_id]

            # Handle different answer types
            if "textAnswers" in answer_obj:
                values = [
                    a["value"] for a in answer_obj["textAnswers"]["answers"]
                ]
                answer_value = "; ".join(values)

            else:
                answer_value = ""

        else:
            answer_value = ""

        answer_map[question_id] = answer_value

    parsed_rows.append(answer_map)

### Finally, match question IDs to question shorthands, and append answers.

# invert shorthand->title to title->shorthand
title_to_short = {title: short for short, title in shortQ_to_titleQ.items()}

# map Google question IDs -> shorthand (when title matches)
idQ_to_shortQ = {}
for qid, title in idQ_to_titleQ.items():
    short = title_to_short.get(title)
    if short:
        idQ_to_shortQ[qid] = short

# build list of responses where keys are shorthand (preserve schema order)
responses_shorthand = []
for row in parsed_rows:
    mapped = {short: "" for short in ordered_shortQ_to_titleQ}
    for qid, ans in row.items():
        short = idQ_to_shortQ.get(qid)
        if short:
            mapped[short] = ans
    responses_shorthand.append(mapped)

print(responses_shorthand)


### Export files in usable formats
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

### Write CSV with shorthand keys as headers, and answers as rows
csv_file = output_dir / "form_responses.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    
    header = list(responses_shorthand[0].keys())
    writer.writerow(header)

    for item in responses_shorthand:
        writer.writerow(list(item.values()))

print(f"CSV written to {csv_file}")

### Write individual JSON files for each response, with shorthand keys
def sanitize_filename(name):
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\-]", "", name)
    return name

for item in responses_shorthand:

    device_name = item.get("device_name")
    filename = sanitize_filename(device_name)

    json_path = output_dir / f"{filename}.json"

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(item, jf, indent=2, ensure_ascii=False)

print(f"JSON files written to {output_dir}")