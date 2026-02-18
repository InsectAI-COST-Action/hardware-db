import os
import json
from datetime import datetime

from googleapiclient.discovery import build

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config


# ----------------------------------------------------------------------
# Declare needed config keys for script's functioning
# ----------------------------------------------------------------------
SCOPES = []
SCHEMA_FILE = ""
GOOGLE_FORM_ID = ""
OAUTH_CLIENT_JSON = ""
TOKEN_CREATE_FORM = ""
DISCOVERY_DOC = ""
DEBUG = False


# ----------------------------------------------------------------------
# Functions for building request body
# ----------------------------------------------------------------------
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

# ==================================================================
# Main fun: call APIs, parse body, etc.
# ==================================================================
def main():
    cfg = build_config(globals())
    
    oauth_path = resolve_oauth_path(cfg["OAUTH_CLIENT_JSON"])
        
    ### Make credentials
    creds = None
    creds = make_creds(
        OAUTH_CLIENT_JSON=oauth_path,
        TOKEN_FILE=cfg["TOKEN_CREATE_FORM"],
        SCOPES=cfg["SCOPES"],
    )
    
    ### Create services with stored credentials
    forms_service = build(
        "forms",
        "v1",
        credentials=creds,
        discoveryServiceUrl=DISCOVERY_DOC,
        static_discovery=False,
        )
    drive_service = build("drive", "v3", credentials=creds)
    
    ### Load schema
    with open(cfg["SCHEMA_FILE"]) as f:
        schema = json.load(f)

    ### 1. Create empty form
    form = forms_service.forms().create(
        body={
            "info": {
                "title": schema["info"]["title"]
            }
        }
    ).execute()

    form_id = form["formId"]
    
    # 1a. Add description and any top‑level settings
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

    # # 1b. settings (email collection, etc.)
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

    ### 2. Create sections + questions (NO logic yet)
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

    ### 3. Map symbolic section IDs → Google itemIds
    section_id_map = {}
    replies = resp["replies"]

    for section_id, item_index in section_positions.items():
        section_id_map[section_id] = replies[item_index]["createItem"]["itemId"]

    ### 4. Patch branching logic (choice questions only)
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

    ### 5. Rename & move Drive file
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
        addParents=cfg["PARENT_DIR"],
        removeParents=previous_parents,
        fields="id, parents"
    ).execute()

    print("Form created successfully:")
    print(f"https://docs.google.com/forms/d/{form_id}/edit")


if __name__ == "__main__":
    main()
