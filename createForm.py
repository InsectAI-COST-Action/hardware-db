from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

creds = Credentials.from_authorized_user_file(
    "token.json",
    scopes=["https://www.googleapis.com/auth/forms.body"]
)

service = build("forms", "v1", credentials=creds)


# ### Create form
# form = service.forms().create(
#     body={"info": {"title": "Test form from API"}}
# ).execute()

# form_id = form["formId"]
form_id = "1b3EvmixvLWugaq8wnKANgeGrWxMC6Dr5V65KkSWbgig" # override ID for testing

### Using batch updates to input questions into form
with open("formtest.json", "r") as f:
    requests = json.load(f)

service.forms().batchUpdate(
    formId=form_id,
    body={"requests": requests}
).execute()
