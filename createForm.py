from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(
    "token.json",
    scopes=["https://www.googleapis.com/auth/forms.body"]
)

service = build("forms", "v1", credentials=creds)


### Create form
form = service.forms().create(
    body={"info": {"title": "Test form from API"}}
).execute()

form_id = form["formId"]
