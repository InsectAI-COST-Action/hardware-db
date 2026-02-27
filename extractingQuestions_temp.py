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

### Sanitise form JSON by removing IDs and other data not needed to re-create form
def sanitise_form(form_json):
    out = {
        "info": {
            "title": form_json["info"].get("title"),
            "description": form_json["info"].get("description")
        },
        "settings": form_json.get("settings", {}),
        "items": []
    }

    for item in form_json.get("items", []):
        clean_item = {}

        # Common fields
        if "title" in item:
            clean_item["title"] = item["title"]
        if "description" in item:
            clean_item["description"] = item["description"]

        # Section
        if "pageBreakItem" in item:
            clean_item["pageBreakItem"] = {}

        # Question
        elif "questionItem" in item:
            q = item["questionItem"]["question"]
            clean_q = {}

            if "required" in q:
                clean_q["required"] = q["required"]

            # Copy question subtype wholesale, minus IDs
            for k in ("textQuestion", "choiceQuestion", "scaleQuestion"):
                if k in q:
                    clean_q[k] = copy.deepcopy(q[k])

            clean_item["questionItem"] = {
                "question": clean_q
            }

        out["items"].append(clean_item)

    return out

with open("extractedForm_temp.json") as f:
    raw = json.load(f)

sanitised = sanitise_form(raw)

with open("sanitised_form.json", "w") as f:
    json.dump(sanitised, f, indent=2)
