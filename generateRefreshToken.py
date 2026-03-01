import os
import json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config

# Path to the client‑secret JSON you downloaded from GCP
OAUTH_CLIENT_JSON = ""
SCOPES = []

cfg = build_config(globals())

oauth_path = resolve_oauth_path(cfg["OAUTH_CLIENT_JSON"])

flow = InstalledAppFlow.from_client_secrets_file(oauth_path, cfg["SCOPES"])
creds = flow.run_local_server(port=0)          # opens a browser, you approve

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

with open(f"tokenRefresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
    json.dump(refresh_blob, f, indent=2)

print("\n=== COPY THIS JSON INTO YOUR GITHUB SECRET ===\n")
print(json.dumps(refresh_blob, indent=2))