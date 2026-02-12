from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import json
import os

from src.authFlow_helpers import resolve_oauth_path

### =====================
### CONFIG
### =====================
DB_VERSION = "v0.2.0"
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive",
]

SCHEMA_FILE = "hardware-db_schema.json"
OAUTH_CLIENT_JSON = resolve_oauth_path()
TOKEN_FILE = "token_createForm.json"
PARENT_DIR = "1UBiv4UnuLzDrOJbOgcRzgwqN2Y4Gv75S" # hardware-db Forms folder
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"


### =====================
### HELPERS
### =====================
def build_choice_options(q, section_id_map=None):
    options = []

    for opt in q["options"]:
        option = {"value": opt}

        # Only resolve logic if section_id_map is provided
        if section_id_map and "logic" in q:
            logic = q["logic"].get(opt)
            if logic:
                target = logic["go_to"]

                if target == "next":
                    option["goToAction"] = "NEXT_SECTION"
                elif target == "submit_form":
                    option["goToAction"] = "SUBMIT_FORM"
                else:
                    option["goToSectionId"] = section_id_map[target]

        options.append(option)

    return options

def build_section_header(section):
    hdr = {"title": section["title"], "pageBreakItem": {}}
    if "description" in section and section["description"]:
        hdr["description"] = section["description"]
    return hdr

def build_question_item(q, section_id_map=None):
    question = {"required": q.get("required", False)}

    if q["type"] == "text":
        question["textQuestion"] = {
            "paragraph": q.get("paragraph", False)
        }

    elif q["type"] == "choice":
        question["choiceQuestion"] = {
            "type": q.get("choiceType", "RADIO"),
            "options": build_choice_options(q, section_id_map)
        }

    elif q["type"] == "scale":
        question["scaleQuestion"] = {
            "low": q["low"],
            "high": q["high"]
        }

    else:
        raise ValueError(f"Unknown question type: {q['type']}")

    item = {"title": q["title"], "questionItem": {"question": question}}
    if "description" in q and q["description"]:
        item["description"] = q["description"]
    return item

def build_batch_requests(items):
    return [
        {
            "createItem": {
                "item": item,
                "location": {"index": idx}
            }
        }
        for idx, item in enumerate(items)
    ]


### =====================
### MAIN
### =====================
def main():
    # Load schema
    with open(SCHEMA_FILE) as f:
        schema = json.load(f)

    # ----------------------------------------------------------------------
    # Authentication flow – supports:
    #   * Fresh token via local server (when you run the script locally)
    #   * Re‑using a stored refresh token (CI)
    # ----------------------------------------------------------------------
    creds = None

    # Try to load a persisted token file (useful when you run locally)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If we have a refresh‑token secret (CI), load it and build Credentials
    if not creds or not creds.valid:
        # Look for the REFRESH_TOKEN_JSON secret (exposed as env var)
        refresh_blob_raw = os.getenv("REFRESH_TOKEN_JSON")
        if refresh_blob_raw:
            try:
                refresh_blob = json.loads(refresh_blob_raw)
                creds = Credentials(
                    token=refresh_blob.get("token"),
                    refresh_token=refresh_blob.get("refresh_token"),
                    token_uri=refresh_blob.get("token_uri"),
                    client_id=refresh_blob.get("client_id"),
                    client_secret=refresh_blob.get("client_secret"),
                    scopes=refresh_blob.get("scopes"),
                )
                # Force a refresh if the access token is expired or missing
                if not creds.valid or creds.expired:
                    creds.refresh(Request())
            except Exception as exc:
                raise RuntimeError(
                    "Failed to parse REFRESH_TOKEN_JSON – ensure the secret contains the full JSON blob."
                ) from exc

    # If we still have no credentials, fall back to the interactive flow (local dev)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, SCOPES)
        creds = flow.run_local_server(port=0)   # opens a browser – only works locally

        # Persist the fresh token for the next local run
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    drive_service = build("drive", "v3", credentials=creds)

    # -------------------------------------------------
    # 1. Create empty form
    # -------------------------------------------------
    form = forms_service.forms().create(
        body={
            "info": {
                "title": schema["info"]["title"]
            }
        }
    ).execute()

    form_id = form["formId"]
    
    # -----------------------------------------------------------------
    # 1b. Add description and any top‑level settings
    # -----------------------------------------------------------------
    form_updates = []

    # description
    if "description" in schema["info"]:
        desc_text = schema["info"]["description"].replace("\\n", "\n")
        form_updates.append({
            "updateFormInfo": {
            "info": {"description": desc_text},
            "updateMask": "description"
            }
        })

    # # settings (email collection, etc.)
    # if "settings" in schema:
    #     # Example: only emailCollectionType is defined in your schema
    #     form_updates.append({
    #         "updateSettings": {
    #             "settings": {
    #                 "emailCollectionType": schema["settings"].get(
    #                     "emailCollectionType", "DO_NOT_COLLECT"
    #                 )
    #             },
    #             "updateMask": "settings.emailCollectionType"
    #         }
    #     })

    if form_updates:
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={"requests": form_updates}
        ).execute()

    # -------------------------------------------------
    # 2. Create sections + questions (NO logic yet)
    # -------------------------------------------------
    items = []
    section_positions = {}  # section_id → index in item list

    for section in schema["sections"]:
        section_positions[section["id"]] = len(items)

        # Section header
        items.append(build_section_header(section))

        # Questions in this section
        for q in section["questions"]:
            items.append(build_question_item(q))

    resp = forms_service.forms().batchUpdate(
        formId=form_id,
        body={"requests": build_batch_requests(items)}
    ).execute()

    # -------------------------------------------------
    # 3. Map symbolic section IDs → Google itemIds
    # -------------------------------------------------
    section_id_map = {}
    replies = resp["replies"]

    for section_id, item_index in section_positions.items():
        section_id_map[section_id] = replies[item_index]["createItem"]["itemId"]

    # -------------------------------------------------
    # 4. Patch branching logic (choice questions only)
    # -------------------------------------------------
    logic_requests = []
    reply_index = 0          # keeps the position of the current item in the form
    section_start_indices = {}   # map section id → first item index (pageBreak)

    for section in schema["sections"]:
        # The pageBreak that starts the section occupies one index
        section_start_indices[section["id"]] = reply_index
        reply_index += 1      # pageBreak itself

        for q in section["questions"]:
            if q["type"] == "choice" and "logic" in q:
                # The item that holds the question is the next index after the pageBreak
                item_id = replies[reply_index]["createItem"]["itemId"]

                # Build the update request – note the added `location`
                logic_requests.append({
                    "updateItem": {
                        "item": {
                            "itemId": item_id,
                            "questionItem": {
                                "question": {
                                    "choiceQuestion": {
                                        "type": q.get("choiceType", "RADIO"),
                                        "options": build_choice_options(q, section_id_map)
                                    }
                                }
                            }
                        },
                        "location": {
                            "index": reply_index
                        },
                        "updateMask": "questionItem.question.choiceQuestion"
                    }
                })
            
            reply_index += 1
    
    if logic_requests:
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={"requests": logic_requests}
        ).execute()

    # -------------------------------------------------
    # 5. Rename & move Drive file
    # -------------------------------------------------
    drive_service.files().update(
        fileId=form_id,
        body={
            "name": f"{datetime.today().strftime('%Y-%m-%d_%H:%M:%S')} "
                    f"- InsectAI hardware database submission form ({DB_VERSION})"
        }
    ).execute()
    
    # Get current parents
    file = drive_service.files().get(
        fileId=form_id,
        fields="parents"
    ).execute()

    previous_parents = ",".join(file.get("parents"))

    # Move the form
    drive_service.files().update(
        fileId=form_id,
        addParents=PARENT_DIR,
        removeParents=previous_parents,
        fields="id, parents"
    ).execute()

    print("Form created successfully:")
    print(f"https://docs.google.com/forms/d/{form_id}/edit")


if __name__ == "__main__":
    main()
