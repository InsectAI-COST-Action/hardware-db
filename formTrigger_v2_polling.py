# formTrigger_v2_polling.py
# Alternative approach: Use Google Forms API to poll for responses
# instead of creating a bound script with triggers

import json, os, sys, urllib.request, urllib.parse, datetime
from authFlow_helpers import resolve_oauth_path, make_creds

# ------------------------------------------------------------
# 1️⃣  CONFIG – edit these values once
# ------------------------------------------------------------
CLIENT_ID      = "169338603256-2thchlcnuosj9jetpube07keuc35ln9v.apps.googleusercontent.com"
CLIENT_SECRET  = "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"
REFRESH_TOKEN  = "1//03q1oLSr819_0CgYIARAAGAMSNwF-L9Ir_IcW5srMf5SI2I90WNzk_GrtOXgDXPWn-MKSs0WpoYXivYca13ikzgz3Rfdn0OCmxUk"
FORM_ID        = "1hg7KuM9BkXK8quQqQXAh4CXQrpT-JazrjKLzKQNgYw8"
TARGET_Q_TITLE = "Previous deviceID"  # exact question text
MATCH_VALUE    = "newDevice"
GITHUB_OWNER   = "InsectAI-COST-Action"
GITHUB_REPO    = "hardware-db"
GITHUB_EVENT   = "new_form_response"
# Note: Scheduling is handled by GitHub Actions workflow (cron: */5 * * * *)
# This script runs once per workflow execution, not in a loop
STATE_FILE = "data/formTrigger_state.json"

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
    try:
        info = urllib.request.urlopen(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
        ).read()
        print("[debug] token info:", info)
    except Exception as e:
        print("[debug] failed to fetch tokeninfo:", e)
    return token

def api_call(method, url, body=None, headers=None):
    default_headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=default_headers)
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

def get_form_structure():
    """Get form metadata to find the target question ID"""
    print("[*] Fetching form structure...")
    form = api_call("GET", f"{FORMS_API}/forms/{FORM_ID}")
    
    # Find the question with TARGET_Q_TITLE
    for item in form.get("items", []):
        if item.get("title") == TARGET_Q_TITLE:
            question_id = item.get("questionItem", {}).get("question", {}).get("questionId")
            print(f"[+] Found target question: {TARGET_Q_TITLE} (ID: {question_id})")
            return question_id
    
    raise ValueError(f"Could not find question '{TARGET_Q_TITLE}' in form")

def get_form_responses(question_id):
    """Fetch all responses from the form"""
    print("[*] Fetching form responses...")
    result = api_call("GET", f"{FORMS_API}/forms/{FORM_ID}/responses")
    return result.get("responses", [])

def extract_answer(response, question_id):
    """Extract the answer to our target question from a response"""
    for answer in response.get("answers", {}).values():
        if answer.get("questionId") == question_id:
            return answer.get("textAnswers", {}).get("answers", [{}])[0].get("value", "")
    return None

def load_state():
    """Load the last processed response ID"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"last_response_id": None, "processed_ids": []}
    return {"last_response_id": None, "processed_ids": []}

def save_state(state):
    """Save the last processed response ID"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def trigger_github_dispatch(form_response_id, answer):
    """Trigger a GitHub Actions workflow_dispatch event"""
    print(f"[*] Triggering GitHub dispatch event...")
    
    github_token = os.environ.get("GH_TOKEN")
    if not github_token:
        print("[!] GH_TOKEN env var not set - skipping GitHub dispatch")
        return False
    
    url = f"{GITHUB_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/dispatches"
    payload = {
        "event_type": GITHUB_EVENT,
        "client_payload": {
            "formId": FORM_ID,
            "responseId": form_response_id,
            "answer": answer,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    }
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Media-Type": "github.v3"
    }
    
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    
    try:
        urllib.request.urlopen(req)
        print(f"[+] GitHub dispatch triggered successfully")
        return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="ignore")
        print(f"[error] GitHub dispatch failed: {e.code} {e.reason}")
        print(f"[error] Response: {error_body}")
        return False

def poll_and_process():
    """Main polling loop"""
    state = load_state()
    question_id = get_form_structure()
    responses = get_form_responses(question_id)
    
    processed_count = 0
    for response in reversed(responses):  # Process oldest first
        response_id = response.get("responseId")
        
        if response_id in state.get("processed_ids", []):
            continue
        
        answer = extract_answer(response, question_id)
        if answer == MATCH_VALUE:
            print(f"[!] Found matching response: {response_id} = '{answer}'")
            if trigger_github_dispatch(response_id, answer):
                state["processed_ids"].append(response_id)
                state["last_response_id"] = response_id
                processed_count += 1
    
    save_state(state)
    
    if processed_count > 0:
        print(f"[+] Processed {processed_count} matching response(s)")
    else:
        print("[*] No new matching responses")

def main():
    TOKEN = get_access_token()
    print(f"[debug] obtained access token")
    print(f"[*] Polling form: {FORM_ID}")
    print(f"[*] Looking for: {TARGET_Q_TITLE} = {MATCH_VALUE}")
    
    try:
        poll_and_process()
    except Exception as e:
        print(f"[error] Polling failed: {e}")
        raise

if __name__ == "__main__":
    main()
