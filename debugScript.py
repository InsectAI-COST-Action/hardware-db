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
    "https://www.googleapis.com/auth/spreadsheets"
]


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

## --------------------------------------------------------------------------------------------- ##
## ---------------------------------------## FUNCTIONS ##--------------------------------------- ##
## --------------------------------------------------------------------------------------------- ##

#### HELPER FUNCTIONS ####

## -------------------- ##
## ---- RESET FORM ---- ##
## -------------------- ##

# ''' def clear_form_items():
#     form = forms_service.forms().get(formId=FORM_ID).execute()
#     items = form.get("items", [])

#     if not items:
#         print("Form already empty.")
#         return

#     delete_requests = [{"deleteItem": {"location": {"index": 0}}} for _ in items]

#     print(f"Deleting {len(delete_requests)} items...")

#     forms_service.forms().batchUpdate(
#         formId=FORM_ID,
#         body={"requests": delete_requests}
#     ).execute()'''

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
    print("Rows extracted:", rows)

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

    print("Form metadata found:", results)

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

def is_row_complete(row):
    """Check if a row has all required fields."""
    return all(row.get(field) for field in REQUIRED_FIELDS)

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
        return {"title": q_text, "description": description, "pageBreakItem": {}}

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

def create_json_info(form_title, doc_title, form_description):
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

    form_item_request = []

    for item in form_body_json:
        if not item:
            continue
        form_item_request.append({
                    "createItem": {
                        "item": item,
                        "location": {"index": 0}
                    }
                }
        )

    form_body_request = {"requests": form_item_request}
    

    try:
        forms_service.forms().batchUpdate(formId=FORM_ID, body=form_info_request).execute()
    except Exception as e:
        print(f"Error updating form info: {e}")

    try:
        forms_service.forms().batchUpdate(formId=FORM_ID, body=form_body_request).execute()
    except Exception as e:
        print(f"Error updating form body: {e}")


    # form = forms_service.forms().get(formId=FORM_ID).execute()    
    # form_request = {"requests": form_body_json}
    # form_created = forms_service.forms().create(body=form_body_json).execute()
    # print("Created form with ID:", form_created["formId"])
    # print("Form updated")
    # forms_service.forms().batchUpdate(formId=FORM_ID, body=form_request).execute()
    print("Form title updated")


def main():
    
    ## RESET FORM
    # clear_form_items()

    ## READ IN INFORMATION FROM THE GOOGLE SHEET
    form_title, doc_title, form_description = read_info_sheet()
    header, rows = read_body_sheet()
    form_info_json = create_json_info(form_title, doc_title, form_description)
    form_body_json = create_json_body(rows)
    create_form(form_info_json, form_body_json)
    read_form()

    ## WRITE INFORMATION FROM THE GOOGLE SHEET INTO A JSON FILE
    # build_json()

    ## DISPLAY INFORMATION FROM GOOGLE SHEET TO CHECK/DEBUG
    ## print("HELLO THIS IS WORKING", doc_title, form_title, form_description)

    # Initialise the file ONLY ONC
    

    
            # json.dump(item, f)

    # print(form_body)


    ## WRITE TO EXISTING FORM ID DECLARED AT THE START OF THE SCRIPT

    
   
if __name__ == "__main__":
    main()