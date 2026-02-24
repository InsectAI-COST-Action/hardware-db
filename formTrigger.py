# formTrigger.py
import json, os, sys, urllib.request, urllib.parse
from authFlow_helpers import resolve_oauth_path, make_creds

# ------------------------------------------------------------
# 1️⃣  CONFIG – edit these values once
# ------------------------------------------------------------
CLIENT_ID      = "169338603256-2thchlcnuosj9jetpube07keuc35ln9v.apps.googleusercontent.com"
CLIENT_SECRET  = "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"
REFRESH_TOKEN  = "1//03WFeWInyc4UTCgYIARAAGAMSNwF-L9IrvwCERs86Qv5GKecVoY-SX0ePUImNDiImWhVUlQLUAFIvcDgBoAdqIxuMO5XYQsJ0wLM"   # obtain via OAuth flow once
FORM_ID        = "1EDkQGRnKg5g6gVP56l6zWwSY7YvrbbM3urdlFcmgQTQ"                # e.g. 1FAIpQLSf...
TARGET_Q_TITLE = "Previous deviceID"         # exact question text
MATCH_VALUE    = "newDevice"
GITHUB_OWNER   = "InsectAI-COST-Action"
GITHUB_REPO    = "hardware-db"
GITHUB_EVENT   = "new_form_response"
# ------------------------------------------------------------

TOKEN_URL = "https://oauth2.googleapis.com/token"
SCRIPT_API = "https://script.googleapis.com/v1"

def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    resp = urllib.request.urlopen(req).read()
    return json.loads(resp)["access_token"]

def api_call(method, url, body=None):
    hdr = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdr)
    return json.loads(urllib.request.urlopen(req).read())

# ------------------------------------------------------------
# 2️⃣  CREATE Apps‑Script project
# ------------------------------------------------------------
TOKEN = get_access_token()
proj = api_call("POST", f"{SCRIPT_API}/projects", {"title": "FormWatcher"})
script_id = proj["scriptId"]
print(f"[+] Created project – scriptId={script_id}")

# ------------------------------------------------------------
# 3️⃣  UPLOAD the handler code
# ------------------------------------------------------------
handler_code = f"""
function onFormSubmit(e) {{
  var target = "{TARGET_Q_TITLE}";
  var match  = "{MATCH_VALUE}";
  var answer = e.namedValues[target] ? e.namedValues[target][0] : "";
  if (answer !== match) return;

  var url = "https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/dispatches";
  var payload = {{
    event_type: "{GITHUB_EVENT}",
    client_payload: {{
      formId: e.response.getId(),
      answer: answer
    }}
  }};
  var opts = {{
    method: "post",
    contentType: "application/json",
    muteHttpExceptions: true,
    headers: {{
      Authorization: "Bearer " + ScriptApp.getOAuthToken(),
      Accept: "application/vnd.github+json"
    }},
    payload: JSON.stringify(payload)
  }};
  UrlFetchApp.fetch(url, opts);
}}
"""
api_call("PATCH",
         f"{SCRIPT_API}/projects/{script_id}/content",
         {"files": [{"name": "Code", "type": "SERVER_JS", "source": handler_code}]})
print("[+] Uploaded onFormSubmit handler")

# ------------------------------------------------------------
# 4️⃣  DEPLOY the script (required for triggers)
# ------------------------------------------------------------
deployment = api_call("POST",
                      f"{SCRIPT_API}/projects/{script_id}/deployments",
                      {"deploymentConfig": {"description": "auto‑trigger"}})
deployment_id = deployment["deploymentId"]
print(f"[+] Deployed – deploymentId={deployment_id}")

# ------------------------------------------------------------
# 5️⃣  CREATE the ON_FORM_SUBMIT trigger bound to the Form
# ------------------------------------------------------------
trigger_body = {
    "eventType": "ON_FORM_SUBMIT",
    "resourceId": FORM_ID
}
trigger = api_call("POST",
                   f"https://script.googleapis.com/v1/scripts/{script_id}:createTrigger",
                   trigger_body)
print("[+] Trigger created –", trigger["trigger"]["triggerId"])