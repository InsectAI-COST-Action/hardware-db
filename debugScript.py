## --------------------------------------------------------------------------------------------- ##
## ------------------------------------### INITIALISATION ##------------------------------------ ##
## --------------------------------------------------------------------------------------------- ##


from __future__ import print_function
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json
import copy

#### CONFIGURATION ####

# Define constants which can be changed depending on form of interest - may change this later to have a basic formID too
FORM_ID = "19htB7BIDoh3ngRtvgURIyCrT1Cir_ScP4lWVnZ-ftHc"
SHEETS_URL = "1DClwffVrkrwH0G5nuCVCJVVoLLdueuqHdJ_VXWPc_Pg"
SHEETS_RANGE = 'Master!A1:R100'
SHEETS_METADATA_RANGE = 'FormSettings!A1:C10'

OAUTH_CLIENT_JSON = "C:/Users/gsmit/OneDrive/Documents/01_Career/03_Academia/05_PhD_Pollinator_diversity/16_STSM/insect-hdb_workspace/oauth_client.json"

# The scope within which the API has been declared to operate i.e. now the forms body can be edited, and so can the whole spreadsheet, but not the forms responses
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

DEBUG = False  # set True to enable verbose item-level debug output

BATCH_SIZE = 50
REQUIRED_FIELDS = ["question", "type", "formItemID"]
FORM_TYPE = "full"

# Optional variable to reset the token if the scope above has changed
user_scope_response = "no" ## TRY BLOCK
creds = None

#### AUTHENTICATION ####
if os.path.exists('token.json') and user_scope_response == "no":
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, scopes=SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

#### API SERVICES ####
sheets_service = build("sheets", "v4", credentials=creds)
forms_service = build("forms", "v1", credentials=creds)
drive_service = build("drive", "v3", credentials=creds)

## --------------------------------------------------------------------------------------------- ##
## ---------------------------------------## FUNCTIONS ##--------------------------------------- ##
## --------------------------------------------------------------------------------------------- ##

#### HELPER FUNCTIONS ####

## -------------------- ##
## ---- RESET FORM ---- ##
## -------------------- ##

def clear_form_items():
    form = forms_service.forms().get(formId=FORM_ID).execute()
    items = form.get("items", [])

    if not items:
        print("Form already empty.")
        return

    delete_requests = [{"deleteItem": {"location": {"index": len(items) - 1 - i}}} for i in range(len(items))]

    print(f"Deleting {len(delete_requests)} items...")

    forms_service.forms().batchUpdate(
        formId=FORM_ID,
        body={"requests": delete_requests}
    ).execute()

## -------------------- ##
## --- READ SHEET(S)--- ##
## -------------------- ##

def read_info_sheet():
    # print("Fetching form metadata...")
    metadata = sheets_service.spreadsheets().values().get(
        spreadsheetId=SHEETS_URL,
        range=SHEETS_METADATA_RANGE
    ).execute()
    
    rows = metadata.get('values', [])
    # print("Rows extracted:", rows)

    if not rows:
        raise ValueError("Sheet metadata missing or incorrect")
    
    header = rows[0]
    structured_rows = [
        {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
        for row in rows[1:]
    ]
    
    # print("Structured rows:", structured_rows)

    # The keys we want to fetch
    keys_to_find = ["formTitle", "docTitle", "formDescription"]
    results = {key: None for key in keys_to_find}

    # Search for each row
    for row in structured_rows:
        first_col = row.get(header[0], "")
        second_col = row.get(header[1], "")
        if first_col == FORM_TYPE and second_col in keys_to_find:
            results[second_col] = row.get(header[2], "")

    # print("Form metadata found:", results)

    form_title = results["formTitle"]
    doc_title = results["docTitle"]
    form_description = results["formDescription"]

    return form_title, doc_title, form_description
    # form_title =
    # form_description = 

def read_body_sheet():
    
    # print("Fetching hardware data...")
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SHEETS_URL,range=SHEETS_RANGE).execute()

    rows = result.get('values', [])
    # print("Rows extracted:", rows)

    if not rows:
        raise ValueError("Sheet is empty or range is incorrect")
    
    header = rows[0]

    structured_rows = [{header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
        for row in rows[1:]]

    return header, structured_rows

def read_form():
    form_existing_json = forms_service.forms().get(formId=FORM_ID).execute()

    with open("./json_existing.json", "w") as f:
        json.dump([], f)
        json.dump(form_existing_json, f, indent=4)    
    
## -------------------- ##
##  BUILD HARDWARE JSON ##
## -------------------- ##

def build_json(row):
    """Convert a row into a Form item JSON compatible with Google Forms API."""
    q_text = str(row.get("question") or "").strip()
    q_type = str(row.get("type") or "").strip().upper()
    required = str(row.get("required", "")).strip().lower() == "true"
    options = [o.strip() for o in str(row.get("options", "")).split(",") if o.strip()]
    description = str(row.get("description") or "").strip()
    item_id = str(row.get("formItemID") or "").strip()
    image_id = str(row.get("imageID") or "").strip()

    # Section / Page Break
    if q_type in ["SECTION", "SECTION_HEADER", "PAGE_BREAK"]:
        return {"itemId": item_id, "title": q_text, "description": description, "pageBreakItem": {}}

    # Skip empty / N/A
    if q_type in ["", "N/A", "NONE"]:
        return None

    item = {"itemId": item_id, "title": q_text, "questionItem": {"question": {"required": required}}}
    
    # Only add image if image_id is not empty
    if image_id:
        item["questionItem"]["image"] = image_id

    if q_type in ["TEXT", "SHORT", "SHORT_TEXT", "FILE_UPLOAD", "FILE UPLOAD"]:
        item["questionItem"]["question"]["textQuestion"] = {"paragraph": False}
    elif q_type in ["PARAGRAPH", "LONG_TEXT", "PARAGRAPH_TEXT"]:
        item["questionItem"]["question"]["textQuestion"] = {"paragraph": True}
    elif q_type in ["MULTIPLE_CHOICE", "MCQ"]:
        item["questionItem"]["question"]["choiceQuestion"] = {"type": "RADIO", "options": [{"value": o} for o in options]}
    elif q_type in ["CHECKBOX", "CHECKBOXES"]:
        item["questionItem"]["question"]["choiceQuestion"] = {"type": "CHECKBOX", "options": [{"value": o} for o in options]}
    elif q_type in ["SCALE", "LINEAR"]:
        item["questionItem"]["question"]["scaleQuestion"] = {"low": 1, "high": 5}
    else:
        raise ValueError(f"Unsupported question type: {q_type}")

    return item

## -------------------- ##
##     JSON HANDLING    ##
## -------------------- ##

def create_json_info(form_title, doc_title, form_description):
    
    # Document title has to be updated directly via the Drive API and this is done here
    rename = drive_service.files().update(
    fileId=FORM_ID,
    body={"name": doc_title},
    fields="id, name"
    ).execute()

    print(f"Updated Drive file name to: {rename['name']}")
    
    form_info_json = {
        "title": form_title,
        "documentTitle": doc_title,
        "description": form_description
    }

    with open("./json_info.json", "w") as f:
        json.dump(form_info_json, f, indent=4)

    return form_info_json

def create_json_body(rows):
    with open("./json_body.json", "w") as f:
        json.dump([], f)
        form_body_json = []
        for row in rows:
            item = build_json(row)
            form_body_json.append(item)
            f.seek(0)
            json.dump(form_body_json, f, indent=4)

    return form_body_json

## -------------------- ##
##     FORM SYNCING     ##
## -------------------- ##

def execute_delete_ops(forms_service, form_id, delete_ops):
	"""Execute delete requests immediately so subsequent move indices are valid."""
	if not delete_ops:
		return
	try:
		forms_service.forms().batchUpdate(formId=form_id, body={"requests": delete_ops}).execute()
		# print(f"Deleted {len(delete_ops)} items")
	except Exception as e:
		print(f"Error deleting items: {e}")

def apply_item_updates(forms_service, form_id, valid_items, existing_items):
    """
    Performs minimal updates while preserving full question structure
    to avoid Google Forms API validation errors.
    """

    def opts_list_from_question(q):
        return [o.get("value") for o in q.get("choiceQuestion", {}).get("options", [])]

    # Maps for lookup
    id_to_item = {it.get("itemId"): it for it in existing_items if it.get("itemId")}
    id_to_index = {it.get("itemId"): i for i, it in enumerate(existing_items) if it.get("itemId")}

    update_ops = []

    for _, desired_item in valid_items:
        item_id = desired_item.get("itemId")
        if not item_id or item_id not in id_to_item:
            print(f"Skipping update: missing or unknown itemId '{item_id}'")
            continue

        existing_item = id_to_item[item_id]
        index = id_to_index[item_id]

        diffs = []

        # Compare title / description
        if (existing_item.get("title") or "") != (desired_item.get("title") or ""):
            diffs.append("title")
        if (existing_item.get("description") or "") != (desired_item.get("description") or ""):
            diffs.append("description")

        # Compare question-level differences
        ex_q = existing_item.get("questionItem", {}).get("question", {}) or {}
        des_q = desired_item.get("questionItem", {}).get("question", {}) or {}

        if ex_q.get("required") != des_q.get("required"):
            diffs.append("question.required")

        if opts_list_from_question(ex_q) != opts_list_from_question(des_q):
            diffs.append("question.options")

        if not diffs:
            continue

        print(f"Updating item {item_id}, diffs={diffs}, index={index}")

        # Start with a *deep copy* of the entire existing item
        update_item = copy.deepcopy(existing_item)
        update_mask_parts = []

        # Patch title / description
        if "title" in diffs:
            update_item["title"] = desired_item.get("title")
            update_mask_parts.append("title")

        if "description" in diffs:
            update_item["description"] = desired_item.get("description")
            update_mask_parts.append("description")

        # Patch inside questionItem
        q_update_target = update_item.get("questionItem", {}).get("question", {})

        # Required
        if "question.required" in diffs:
            q_update_target["required"] = bool(des_q.get("required"))
            update_mask_parts.append("questionItem.question.required")

        # Options
        if "question.options" in diffs:
            desired_choice = des_q.get("choiceQuestion", {})
            if desired_choice:
                q_update_target["choiceQuestion"] = desired_choice
                update_mask_parts.append("questionItem.question.choiceQuestion.options")

        # Build the update request
        update_ops.append({
            "updateItem": {
                "item": update_item,
                "location": {"index": index},
                "updateMask": ",".join(update_mask_parts)
            }
        })

        print("Prepared updateItem:", json.dumps(update_ops[-1], indent=2))

    # Execute all update ops
    if not update_ops:
        print("No item updates needed.")
        return 0

    try:
        forms_service.forms().batchUpdate(formId=form_id, body={"requests": update_ops}).execute()
        print(f"Applied {len(update_ops)} item updates")
        return len(update_ops)
    except Exception as e:
        print("ERROR applying updates:", e)
        print(json.dumps(update_ops, indent=2))
        return 0

def simulate_operations(valid_items, existing_items):
	"""
	Simulate sequential moves and creates on a local current_order list to produce valid
	'moveItem' and 'createItem' requests. Returns form_requests (list).
	"""
	current_order = [it.get("itemId") for it in existing_items]
	form_requests = []
	valid_items_sorted = sorted(valid_items, key=lambda x: x[0])

	for desired_idx, item in valid_items_sorted:
		# validate desired_idx
		if desired_idx is None or desired_idx < 0:
			continue
		if desired_idx > len(current_order):
			desired_idx = len(current_order)

		item_id = item.get("itemId", "")
		if item_id and item_id in current_order:
			old_idx = current_order.index(item_id)
			if old_idx != desired_idx:
				form_requests.append({
					"moveItem": {
						"originalLocation": {"index": int(old_idx)},
						"newLocation": {"index": int(desired_idx)}
					}
				})
				# simulate move
				val = current_order.pop(old_idx)
				current_order.insert(desired_idx, val)
		else:
			# create (use item as-is; JSON should provide itemId when authoritative)
			form_requests.append({
				"createItem": {
					"item": item,
					"location": {"index": int(desired_idx)}
				}
			})
			# simulate insertion: if item has itemId, insert it so later ops can reference it
			current_order.insert(desired_idx, item_id or f"_tmp_{len(current_order)}")

	return form_requests

def apply_moves_creates(forms_service, form_id, form_info_request, form_requests):
	"""Apply form info update (already minimal) and the moves/creates batch; return counts summary."""
	# apply form info (title/description)
	try:
		forms_service.forms().batchUpdate(formId=form_id, body=form_info_request).execute()
	except Exception as e:
		print(f"Error updating form info: {e}")

	if not form_requests:
		# nothing else to do
		return {"moves": 0, "creates": 0, "total": 0}

	form_body_request = {"requests": form_requests}
	try:
		resp = forms_service.forms().batchUpdate(formId=form_id, body=form_body_request).execute()
		replies = resp.get("replies", []) if resp else []
		moves = sum(1 for r in replies if "moveItem" in r)
		creates = sum(1 for r in replies if "createItem" in r)
		# print(f"Applied batch: moves={moves}, creates={creates}, total_replies={len(replies)}")
		return {"moves": moves, "creates": creates, "total": len(replies)}
	except Exception as e:
		# print(f"Error updating form body: {e}")
		return {"moves": 0, "creates": 0, "total": 0}

def create_form(form_info_json, form_body_json):

    with open("./json_form.json", "w") as f:
        json.dump([], f)
        form_json = {
        "formId": FORM_ID,
        "info": form_info_json,
        "settings": {"emailCollectionType": "DO_NOT_COLLECT"},
        "items": form_body_json,
        "revisionId": "",
        "publishSettings": {"publishState": {"isAcceptingResponses": False, "isPublished" : False}}
        }
        json.dump(form_json, f, indent=4)
        json.dump(form_json, f, indent=4)
    
    form_info_request = {
        "requests": [
            {
                "updateFormInfo": {
                    "info": {
                        "title": form_info_json["title"],
                        "description": form_info_json["description"]
                    },
                    "updateMask": "title,description"
                }
            }
        ]
    }

    # Fetch existing form
    existing_form = forms_service.forms().get(formId=FORM_ID).execute()
    existing_items = existing_form.get("items", [])
    existing_ids = {item.get("itemId"): idx for idx, item in enumerate(existing_items)}

    # Filter out None items from form_body_json
    valid_items = [(idx, item) for idx, item in enumerate(form_body_json) if item]
    new_ids = {item.get("itemId"): idx for idx, item in valid_items}

    # Step 1: Delete items not present in JSON
    delete_ops = []
    for existing_id in sorted(existing_ids.keys(), key=lambda x: existing_ids[x], reverse=True):
        if existing_id and existing_id not in new_ids:
            # find index once
            index = existing_ids.get(existing_id)
            if index is not None:
                delete_ops.append({"deleteItem": {"location": {"index": index}}})

    # execute deletes and refresh
    execute_delete_ops(forms_service, FORM_ID, delete_ops)
    existing_form = forms_service.forms().get(formId=FORM_ID).execute()
    existing_items = existing_form.get("items", [])
    # Step 2: apply per-item content updates
    apply_item_updates(forms_service, FORM_ID, valid_items, existing_items)
    # refresh items for accurate indices
    existing_form = forms_service.forms().get(formId=FORM_ID).execute()
    existing_items = existing_form.get("items", [])
    # Step 3: simulate moves/creates and apply them
    form_requests = simulate_operations(valid_items, existing_items)
    summary = apply_moves_creates(forms_service, FORM_ID, form_info_request, form_requests)

    # print(f"Form sync complete: {summary}")

def main():
    
    ## READ IN INFORMATION FROM THE GOOGLE SHEET
    form_title, doc_title, form_description = read_info_sheet()
    header, rows = read_body_sheet()
    form_info_json = create_json_info(form_title, doc_title, form_description)
    form_body_json = create_json_body(rows)
    create_form(form_info_json, form_body_json)
    read_form()

   
if __name__ == "__main__":
    main()