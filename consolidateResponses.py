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
FORM_ID_BASIC = "1mXaEkw1lydgeE5Ld0X5j2Xp82ABDgnQeQ79CvEJi_UQ"
FORM_ID_BASIC_FEEDBACK = "11eU2nSwDg7_2bFFInmzp71FMTqjPvFI03hMfZeZMbI0"
FORM_ID_FULL = "1k7RsEdOJrLW6ZDwOTHNdgDH2VSYWETfCI-1HyznB0m8"
FORM_ID_FULL_FEEDBACK = "1S4wOnE0gNqLgvtut66M-lH4q2VxG4joJMSssi8CGCOM"
FORM_ID_DEPLOYMENT = "19htB7BIDoh3ngRtvgURIyCrT1Cir_ScP4lWVnZ-ftHc"
FORM_ID_DEPLOYMENT_FEEDBACK = "1dYnkrfRVaOM1Trf8BpCP-mDgq1DlnDQ73S8H2-Z-UCA"
    
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
    "https://www.googleapis.com/auth/drive.files"
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

def get_form_items(form_id, forms_service):
    form = forms_service.forms().get(formId=form_id).execute()
    items = form.get("items", [])
    flat = {}

    def walk(items):
        for item in items:
            if "itemId" in item and "title" in item:
                flat[item["itemId"]] = item["title"]
            if "items" in item:
                walk(item["items"])

    walk(items)
    return flat

def get_responses(form_id, forms_service):
    responses = forms_service.forms().responses().list(formId=form_id).execute()
    return responses.get("responses", [])


full_responses = get_responses(FORM_ID, forms_service)
basic_responses = get_responses(FORM_ID, forms_service)

def main():
    
    ## READ IN INFORMATION FROM THE GOOGLE SHEET
    full_form_items = get_form_items(FORM_ID, forms_service)
    schema_item_ids = list(full_form_items.keys())
    schema_headers = [full_form_items[i] for i in schema_item_ids]

    

   
if __name__ == "__main__":
    main()