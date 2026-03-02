# get_edit_response_url.py
# ------------------------------------------------------------
# Retrieve an “edit response” URL for a given Google Form response.
# ------------------------------------------------------------

import json
import os
import sys
import urllib.request
import urllib.error

from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
FORMS_API = "https://forms.googleapis.com/v1"

FORM_ID = "1hg7KuM9BkXK8quQqQXAh4CXQrpT-JazrjKLzKQNgYw8"
RESPONSE_ID = "ACYDBNiTS_K1HYG-8Lq7XRNw3cAIQvjeM8U75L6YbMWfMEdGw85A-iUcnF6KEH3JzQqdoIE"
# OAUTH_CLIENT_JSON = ""
TOKEN_FILE = "D:\\hardware-db\\tokenEditResponse.json"


def api_get(url, token):
    """Simple GET wrapper that returns the parsed JSON."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="ignore")
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        print(err)
        sys.exit(1)


def list_response_ids(form_id, token):
    """Return a list of all responseId strings for *form_id*."""
    url = f"{FORMS_API}/forms/{form_id}/responses"
    data = api_get(url, token)
    # `responses` is a list of objects, each has a `responseId`
    return [r.get("responseId") for r in data.get("responses", [])]


def get_edit_response_url(form_id, response_id, token):
    """
    Build the edit‑URL for a specific response.

    Google Forms exposes the raw response via:
        GET https://forms.googleapis.com/v1/forms/{formId}/responses/{responseId}

    The edit link follows the pattern:
        https://docs.google.com/forms/d/{FORM_ID}/edit#response={RESPONSE_ID}
    """
    
    # Optional: fetch the response to verify it exists (and to illustrate the API call)
    _ = api_get(f"{FORMS_API}/forms/{form_id}/responses/{response_id}", token)

    edit_url = (
        f"https://docs.google.com/forms/d/{form_id}"
        f"/edit#response={response_id}"
    )
    return edit_url


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
def main():
    # --------------------------------------------------------------------
    # Load configuration – works exactly like the other scripts.
    # You can set these values via:
    #   • CLI args   (--FORM_ID xxx --RESPONSE_ID yyy)
    #   • Environment variables (FORM_ID, RESPONSE_ID, OAUTH_CLIENT_JSON, TOKEN_FILE)
    #   • .env / .secrets files in the repo root
    # --------------------------------------------------------------------
    cfg = build_config(globals())

    # Required keys – raise a clear error if missing
    required = ["FORM_ID", "RESPONSE_ID", "OAUTH_CLIENT_JSON", "TOKEN_FILE"]
    for k in required:
        if not cfg.get(k):
            print(f"[ERROR] Missing required config key: {k}")
            sys.exit(1)

    # --------------------------------------------------------------------
    # Build OAuth credentials and obtain a fresh access token
    # --------------------------------------------------------------------
    oauth_path = resolve_oauth_path(cfg["OAUTH_CLIENT_JSON"])
    creds = make_creds(
        OAUTH_CLIENT_JSON=oauth_path,
        TOKEN_FILE=cfg["TOKEN_FILE"],
        SCOPES=[
            "https://www.googleapis.com/auth/forms.responses.readonly",
        ],
    )

    if not creds.valid:
        creds.refresh(Request())
    token = creds.token
   
    # --------------------------------------------------------
    # Fetch and print IDs
    # --------------------------------------------------------
    ids = list_response_ids(FORM_ID, token)

    if not ids:
        print("No responses found for this form.")
    else:
        print("\nResponse IDs:")
        for i, rid in enumerate(ids, 1):
            print(f"{i:3}. {rid}")
    
    # --------------------------------------------------------------------
    # Compute and print the edit URL
    # --------------------------------------------------------------------
    edit_url = get_edit_response_url(
        form_id=FORM_ID,
        response_id=RESPONSE_ID,
        token=token,
    )
    print("\nEdit‑response URL:")
    print(edit_url)


if __name__ == "__main__":
    main()