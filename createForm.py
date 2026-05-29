import os
import json
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config


# ----------------------------------------------------------------------
# Declare needed config keys for script's functioning
# ----------------------------------------------------------------------
# DB_VERSION = "v0.2.0"
SCOPES = []
SCHEMA_FILE = ""
GOOGLE_FORM_ID = ""
PARENT_DIR = ""
OAUTH_CLIENT_JSON = ""
TOKEN_CREATE_FORM = ""
DISCOVERY_DOC = ""
DEBUG = False
UPDATE_LINKS = False


# ----------------------------------------------------------------------
# Functions for building request body
# ----------------------------------------------------------------------
def build_choice_options(q, section_id_map=None):
    options = []
    is_other_flags = q.get("isOther", [])

    for idx, opt in enumerate(q["options"]):
        is_other = idx < len(is_other_flags) and is_other_flags[idx]

        # Google Forms API forbids setting 'value' when 'isOther' is true
        if is_other:
            option = {"isOther": True}
        else:
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

# ----------------------------------------------------------------------
# Functions to update .env and README
# ----------------------------------------------------------------------
def write_form_id_to_env(form_id: str, env_file: str = ".env"):
    """Write the form ID to the GOOGLE_FORM_ID variable in .env file."""
    env_path = Path(env_file)
    
    if not env_path.exists():
        # Create new .env file if it doesn't exist
        with env_path.open("w") as f:
            f.write(f"GOOGLE_FORM_ID={form_id}\n")
        return
    
    # Read the existing file
    lines = []
    found = False
    with env_path.open("r") as f:
        for line in f:
            if line.startswith("GOOGLE_FORM_ID="):
                lines.append(f"GOOGLE_FORM_ID={form_id}\n")
                found = True
            else:
                lines.append(line)
    
    # If GOOGLE_FORM_ID wasn't found, append it
    if not found:
        lines.append(f"GOOGLE_FORM_ID={form_id}\n")
    
    # Write back
    with env_path.open("w") as f:
        f.writelines(lines)

def update_readme_form_link(form_id: str, readme_file: str = "README.md"):
    """Update the form link in README.md between the GOOGLE_FORM_ID markers."""
    readme_path = Path(readme_file)
    
    if not readme_path.exists():
        print(f"Warning: {readme_file} not found, skipping README update")
        return
    
    # Generate the new form link
    new_link = f"https://docs.google.com/forms/d/{form_id}/viewform"
    
    # Read the file
    content = readme_path.read_text()
    
    # Find and replace the link between the markers
    begin_marker = "<!-- GOOGLE_FORM_ID-BEGIN comment to anchor auto-update of form link -->"
    end_marker = "<!-- GOOGLE_FORM_ID-END comment to anchor auto-update of form link -->"
    
    if begin_marker not in content or end_marker not in content:
        print(f"Warning: Form ID markers not found in {readme_file}, skipping README update")
        return
    
    # Extract parts before, between, and after the markers
    before = content[:content.find(begin_marker) + len(begin_marker)]
    after = content[content.find(end_marker):]
    
    # Reconstruct with new link
    new_content = before + f"\n{new_link}\n" + after
    
    readme_path.write_text(new_content)


def write_form_config_to_docs(form_id: str, forms_service, schema: dict, docs_dir: str = "docs"):
    """Write form config JSON for the GitHub Pages landing page."""
    docs_path = Path(docs_dir)
    docs_path.mkdir(exist_ok=True)

    config = {
        "form_id": form_id,
        "form_url": f"https://docs.google.com/forms/d/{form_id}/viewform",
        "entry_ids": {}
    }

    # Find the title of the previous_deviceID question in the schema
    target_title = None
    for section in schema.get("sections", []):
        for q in section.get("questions", []):
            if q.get("id") == "previous_deviceID":
                target_title = q.get("title")
                break

    # Fetch the live form to get question IDs for pre-fill URL construction
    if target_title:
        try:
            form_data = forms_service.forms().get(formId=form_id).execute()
            for item in form_data.get("items", []):
                if "questionItem" in item and item.get("title") == target_title:
                    qid = item["questionItem"]["question"]["questionId"]
                    config["entry_ids"]["previous_deviceID"] = qid
                    break
        except Exception as e:
            print(f"Warning: could not fetch question IDs for pre-fill URLs: {e}")

    config_path = docs_path / "form_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"Form config written to {config_path}")


# ----------------------------------------------------------------------
# Main fun: call APIs, parse body, etc.
# ----------------------------------------------------------------------
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
        discoveryServiceUrl=cfg["DISCOVERY_DOC"],
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
        for q in section.get("questions", []):
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

        for q in section.get("questions", []):
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
                    # f"- InsectAI hardware database submission form ({DB_VERSION})"
                    f"- InsectAI hardware database submission form (v0.2.0)"
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
    
    # Check if links should be updated
    if cfg["UPDATE_LINKS"]:
        write_form_id_to_env(form_id)   # Write form ID to .env
        update_readme_form_link(form_id)   # Update link in README
        write_form_config_to_docs(form_id, forms_service, schema)   # Write landing page config

    print("Form created successfully:")
    print(f"https://docs.google.com/forms/d/{form_id}/edit")


if __name__ == "__main__":
    main()
