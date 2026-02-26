# formTrigger.py
import json, os, sys, urllib.request, urllib.parse
from authFlow_helpers import resolve_oauth_path, make_creds

# ------------------------------------------------------------
# 1️⃣  CONFIG – edit these values once
# ------------------------------------------------------------
CLIENT_ID      = "169338603256-2thchlcnuosj9jetpube07keuc35ln9v.apps.googleusercontent.com"
CLIENT_SECRET  = "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"
REFRESH_TOKEN  = "1//03q1oLSr819_0CgYIARAAGAMSNwF-L9Ir_IcW5srMf5SI2I90WNzk_GrtOXgDXPWn-MKSs0WpoYXivYca13ikzgz3Rfdn0OCmxUk"   # obtain via OAuth flow once
FORM_ID        = "1EDkQGRnKg5g6gVP56l6zWwSY7YvrbbM3urdlFcmgQTQ" # e.g. 1FAIpQLSf...
TARGET_Q_TITLE = "Previous deviceID"  # exact question text
MATCH_VALUE    = "newDevice"
GITHUB_OWNER   = "InsectAI-COST-Action"
GITHUB_REPO    = "hardware-db"
GITHUB_EVENT   = "new_form_response"
# ------------------------------------------------------------

TOKEN_URL = "https://oauth2.googleapis.com/token"
SCRIPT_API = "https://script.googleapis.com/v1"
SCRIPT_MGMT_API = "https://scriptmanagement.googleapis.com/v1"

def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    resp = urllib.request.urlopen(req).read()
    token = json.loads(resp)["access_token"]
    # debug: inspect token scopes
    try:
        info = urllib.request.urlopen(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
        ).read()
        print("[debug] token info:", info)
    except Exception as e:
        print("[debug] failed to fetch tokeninfo:", e)
    return token

def api_call(method, url, body=None):
    hdr = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdr)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(errors="ignore") if hasattr(exc, 'read') else None
        print(f"\n[error] API call failed: {exc.code} {exc.reason}")
        print(f"[error] URL: {url}")
        print(f"[error] Method: {method}")
        if error_body:
            print(f"[error] Response body: {error_body}")
        raise

# ------------------------------------------------------------
# 2️⃣  CREATE Apps‑Script project
# ------------------------------------------------------------
TOKEN = get_access_token()
print("[debug] obtained access token, now attempting API call...")
try:
    proj = api_call("POST", f"{SCRIPT_API}/projects", {"title": "FormWatcher"})
except urllib.error.HTTPError as exc:
    body = exc.read().decode(errors="ignore") if hasattr(exc, 'read') else None
    print(f"[error] API request failed {exc.code} {exc.reason}")
    if body:
        print("response body:", body)
    raise
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
api_call(
    "PUT",
    f"{SCRIPT_MGMT_API}/projects/{script_id}/content",
    {
        "files": [
            {"name": "appsscript", "type": "JSON", "source": '{"timeZone":"America/New_York","exceptionLogging":"STACKDRIVER","runtimeVersion":"V8"}'},
            {"name": "Code", "type": "SERVER_JS", "source": handler_code}
        ]
    }
    )
print("[+] Uploaded onFormSubmit handler")

# ------------------------------------------------------------
# 4️⃣  CREATE a version and DEPLOY the script (required for triggers)
# ------------------------------------------------------------
version = api_call("POST",
                   f"{SCRIPT_MGMT_API}/projects/{script_id}/versions",
                   {})
version_number = version["versionNumber"]
print(f"[+] Created version – versionNumber={version_number}")

deployment = api_call("POST",
                      f"{SCRIPT_MGMT_API}/projects/{script_id}/deployments",
                      {"versionNumber": version_number, "description": "auto-trigger"})
deployment_id = deployment["deploymentId"]
print(f"[+] Deployed – deploymentId={deployment_id}")

# ------------------------------------------------------------
# 5️⃣  CREATE the ON_FORM_SUBMIT trigger bound to the Form
# ⚠️ NOTE: Trigger creation via REST API is not directly supported
#    You must manually create the trigger:
#    1. Go to the Apps Script editor for this project
#    2. Click "Triggers" (left sidebar, clock icon)  
#    3. Click "Create new trigger"
#    4. Set event type to "On form submit"
#    5. Select your form from the dropdown
# ------------------------------------------------------------
print("""
[!] Script deployment complete!

📝 Next steps to activate the trigger:
   1. Visit: https://script.google.com/home/projects/{}/edit
   2. Click the "Triggers" icon (⏰) on the left sidebar
   3. Click "Create new trigger"
      - Function: onFormSubmit
      - Event type: On form submit
      - Form: Select your Google Form
   4. Save and authorize

Then, when forms are submitted with "{}" = "{}", 
the GitHub dispatch event will trigger.
""".format(script_id, TARGET_Q_TITLE, MATCH_VALUE))