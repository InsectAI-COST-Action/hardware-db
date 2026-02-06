from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import json

### Variables
DB_VERSION = "v0.1"

### Functions
def build_question_item(q):
    question = {"required": q.get("required", False)}

    if q["type"] == "text":
        question["textQuestion"] = {
            "paragraph": q.get("paragraph", False)
        }

    elif q["type"] == "choice":
        question["choiceQuestion"] = {
            "type": q.get("choiceType", "RADIO"),
            "options": [{"value": opt} for opt in q["options"]]
        }

    elif q["type"] == "scale":
        question["scaleQuestion"] = {
            "low": q["low"],
            "high": q["high"]
        }

    else:
        raise ValueError(f"Unknown question type: {q['type']}")

    return {
        "title": q["title"],
        "questionItem": {"question": question}
    }

def build_section_item(section):
    return {
        "title": section["title"],
        "pageBreakItem": {}
    }

def flatten_form(schema):
    items = []

    for section in schema["sections"]:
        # Section header
        items.append(build_section_item(section))

        # Section questions
        for q in section.get("questions", []):
            items.append(build_question_item(q))

    return items

def build_batch_requests(items):
    requests = []
    for idx, item in enumerate(items):
        requests.append({
            "createItem": {
                "item": item,
                "location": {"index": idx}
            }
        })
    return requests

### Load JSON schema & authenticate
with open("hardware-db_schema.json") as f:
    schema = json.load(f)

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
    body={
        "info": {
            "title": schema["info"]["title"],
            # "description": schema["info"].get("description", "") ## I'LL NEED TO ADD IT BACK LATER WITH batchUpdate()
        }
    }
).execute()

form_id = form["formId"]
# form_id = "1b3EvmixvLWugaq8wnKANgeGrWxMC6Dr5V65KkSWbgig" # override ID for testing

### Build items
items = flatten_form(schema)
requests = build_batch_requests(items)

### Apply structure
forms_service.forms().batchUpdate(
    formId=form_id,
    body={"requests": requests}
).execute()

# ### Using batch updates to input questions into form
# with open("formMultisectionTest.json", "r") as f:
#     requests = json.load(f)
# 
# forms_service.forms().batchUpdate(
#     formId=form_id,
#     body={"requests": requests}
# ).execute()

### Rename the form in Drive
drive_service.files().update(
    fileId=form_id,
    body={
        "name": f"{datetime.today().strftime('%Y-%m-%d_%H:%M:%S')} - InsectAI hardware database submission form, {DB_VERSION}"
    }
).execute()
