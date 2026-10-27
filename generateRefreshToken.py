import os
import json
from datetime import datetime
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

### This script only takes arguments specified below
### It does not use the helpers in configParsing or authFlow_helpers

# Path to the client‑secret JSON you downloaded from GCP
PROJECT_ROOT = Path(__file__).resolve().parent
OAUTH_CLIENT_JSON = PROJECT_ROOT / "OAuth_client-new.json"
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
]

flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_JSON), SCOPES)
creds = flow.run_local_server(port=0) # opens a browser, you approve

# The Credentials object already contains a refresh token.
# Serialize the *whole* credential (access token, refresh token, expiry, etc.).
refresh_blob = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": creds.scopes,
}

token_path = PROJECT_ROOT / f"tokenRefresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with token_path.open("w", encoding="utf-8") as f:
    json.dump(refresh_blob, f, indent=2)

print("\n=== COPY THIS JSON INTO YOUR GITHUB SECRET ===\n")
print(json.dumps(refresh_blob, indent=2))