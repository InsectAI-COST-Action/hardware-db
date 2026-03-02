[![Tests](https://github.com/InsectAI-COST-Action/hardware-db/actions/workflows/tests.yml/badge.svg)](https://github.com/InsectAI-COST-Action/hardware-db/actions/workflows/tests.yml)

# Insect AI Hardware Database

<p align="center">
**🚧 Under construction! 🚧**
</p>
<p align="center">
<img src="./assets/Hardware-dtb-image.png" width="540"/>
</p>

For progress see [Development notes](DevNotes), [TODO](TODO) and [CHANGELOG](CHANGELOG).


# Quickstart
## Contribute data 
If you want to submit a device to the database, you can find the form here: 
<!-- GOOGLE_FORM_ID-BEGIN comment to anchor auto-update of form link -->
https://docs.google.com/forms/d/13MoXha8YHzm_5Rp1CDhQ95ZPNpp69H81Vv9VAfHfSK8/viewform
<!-- GOOGLE_FORM_ID-END comment to anchor auto-update of form link -->

Form w/ responses for testing: https://docs.google.com/forms/d/e/1FAIpQLSd_qqcBcWHkN7p1yZeIcECoQHG3Ow7fB0cCYU-zKObfeDm60g/viewform?usp=dialog

## Visualise data
If you want to see the visualisation fo the data, you can click here: 
<!-- FRONTEND-BEGIN comment to anchor auto-update of form link -->
*...link coming soon...*
<!-- FRONTEND-END comment to anchor auto-update of form link -->

# Documentation
Below we explain what does what in the repository and how to use it. 
If you only want to contribute or read data, you should not need to read this section. 

<!-- ### Beginning of spoiler section -->
<details>
  <summary>Expand section</summary>

## Intro
The workflow is, at its most basic: 
```
hardware-db_schema.json --- createForms.py ---> Google Form
Google Form --- collectResponses.py ---> data/ (JSON, CSV)
```

The repo is set up to run certain workflows automatically, but if you want to run things locally you will need to install it. 

### Install locally
What you need before getting started: 
 - Python >3.11

All of the required third‑party libraries are declared in `pyproject.toml` so you can use `pip` directly; no conda/mamba environment is required.

You can clone the repo and install the package into a fresh virtual environment:

**Windows**
```powershell
git clone https://github.com/InsectAI-COST-Action/hardware-db.git
chdir hardware-db
python -m venv .venv
.venv\Scripts\activate      # activate the venv
pip install -e .            # runtime dependencies only
```

**Linux/MacOS**
```bash
git clone https://github.com/InsectAI-COST-Action/hardware-db.git
cd hardware-db
python3 -m venv .venv
pip install -e .
```

If you are running tests or building inside GitHub Actions you can install the extra dependencies with the `ci` extra:

```powershell
pip install -e .[ci]        # installs jsonschema etc. for CI/test runs
```

Anytime you close / reopen the terminal, make sure the virtual environment is properly loaded: 

**Windows**
```PowerShell
.venv\Scripts\activate
```

**Linux/MacOS**
```bash
source .venv/bin/activate
```

## The database schema
We store the main database ontology in `hardware-db_schema.json`. This is a modified version of Google Forms API schema to make it easier to edit by hand. 

Example of valid JSON schema:
```json
{
    "info": {
        "title": "The form title here (not the file name)",
        "description": "You description here."
    },
    "settings": {
        "emailCollectionType": "DO_NOT_COLLECT"
    },
    "sections": [
        {
            "id": "sec1",
            "title": "Section 1",
            "description": null,
            "questions": [
                {
                    "id": "q1",
                    "title": "Question 1",
                    "required": true,
                    "type": "choice",
                    "choiceType": "RADIO",
                    "options": [
                        "Yes",
                        "No"
                    ]
                },
                {
                    "id": "q2",
                    "title": "Question 2",
                    "required": true,
                    "type": "text",
                    "paragraph": false
                }
            ]
        },
        {
            "id": "sec2",
            "title": "Section 2",
            "description": "Your section description here.",
            "questions": [
                {
                    "id": "q3",
                    "title": "Question 3",
                    "required": true,
                    "type": "text",
                    "paragraph": false
                }
            ]
        }
    ]
}
```

The syntax is as follows: 
 - There's an `info` block, that contains general details for form. 
 - This is followed by `settings` (currently only manages whether sign-in is required). 
 - Then there's the `section` block, that takes a unique `id` and other details.
 - Nested within `section`, there's `questions`, that itself takes a unique `id` and the question, its description and type as well as allowed options (for some types). 

The terms in the schema map to Google Forms API's terms like so: 

| JSON schema    | Google Forms API   |
| -------------- | ------------------ |
| `form.title`   | `info.title`       |
| `sections[]`   | `pageBreakItem`    |
| `questions[]`  | `questionItem`     |
| Question order | insertion order    |
| Section order  | insertion order    |
| Symbolic `id`  | not sent to Google |

Importantly, the `id` field is what we use to collect the answers, as a shorthand for the question itself, and it needs to be unique. 

### Logic navigation
For now, *only choice questions is supported*, and maps onto Google API like this:
| JSON schema    | Google Forms API                      | Meaning              |
| -------------- | ------------------------------------- | -------------------- |
| `"section_id"` | `goToSectionId: "<pageBreak itemId>"` | Jump to that section |
| `"next"`       | `goToAction: "NEXT_SECTION"`          | Go to next section   |
| `"submit"`     | `goToAction: "SUBMIT_FORM"`           | Submit form          |

The current implementation does two passes of the form, because the API only allows redirection to a specific sectionID, and these are non-meaningful (i.e. created on the fly), so you need to query the form you just created to retrieve these ids and then apply the logic to them. 

### Mandatory fields
In an effort to align with other existing hardware repositories, we align our required field with [Wildlabs' Inventory](https://wildlabs.net/inventory). 
Below the mapping in out schema to their naming. 

| InsectAI `hardware-db` | Wildlabs' Inventory             |
| ---------------------- | ------------------------------- |
| `contact_name`         | `Name` (collected via sign-in)  |
| `contact_email`        | `Email` (collected via sign-in) |
| `device_name`          | `Product_name`                  |
| `device_description`   | `Overview`                      |


# Authenticating in Google APIs
We only support regular OAuth2 authentication via personal access token, not via service account tokens. This is because personal Google accounts (i.e. non-GSuite, non-Workspace accounts) cannot grant service accounts Drive storage space, and this creates issues with managing forms and responses. 

We support both local and CI/CD deployments, and there are a few parts to it:
 - Helper functions in `src/`
    - `src/authFlow_helpers.py` handles the tokens generated in Google API dashboard; these can be saved on your machine as `.json` file, or saved as a repository secret on Github (see below for info on how to set secrets on Github). 
    - `src/configParsing.py` looks in various places for the info needed to authenticate and run the scripts. Importantly, you can call the scripts with arguments in CLI, or supply values with environmental variables or `.env` file (see next section); the order of precedence is: 
      1. CLI argument (if not None)
      2. Environment variable (if present)
      3. .secrets and .env file entry (if present)
      4. Hardcoded defaults for some variables (e.g. debug, secrets-file)

## Secrets and environmental variables

### Local
To avoid hosting in the repo sensitive information, the OAuth access tokens are stored locally in a `.secrets` file. The format is simply

```bash
OAUTH_CLIENT_JSON=path_to_file
TOKEN_TEST_AUTH=path_to_file
```

...and so on. The helper functions will try to resolve the path and read the content of the JSON file with your access tokens. 

The file `.env` contains non-sensitive information, like the permissions to be granted to the API, and locations of the form, etc. It is structured in a similar way as the `.secrets` file. 
The parser `src/configParsing.py` attempts to coerce values into sensible types (i.e. string, boolean, etc) and passes them to the caller as a dictionary. 

### CI/CD workflows
When using CD/CI runners, like Github Actions, we can pass the authentication information via Github's [Repository Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets). 

Basically, you name a secret variable appropriately, `OAUTH_CLIENT_JSON` and `REFRESH TOKEN` in our case, and paste the content of the your JSON file into it. This variables are made available to Github Action runners via the construct `OAUTH_CLIENT_JSON: ${{ secrets.OAUTH_CLIENT_JSON }}`. 

To generate the refresh token that Github needs, you can run the script `generateRefreshToken.py` locally, and paste its output into a repository secret in Github.

Environmental variables can be assigned directly in the workflow, but if not they will fall back to the `.env` file that is available in the repo. 


# Using Google API to manage forms and responses
There are two scripts responsible for creating the form based on the schema, and collecting the answers.

## Creating the form
`createForm.py` uses helpers in `src/configParsing.py` and `src/authFlow_helpers.py` to create authenticate with [Google Forms API](https://developers.google.com/workspace/forms/api/reference/rest), and create the form based on `hardware-db_schema.json`. 

The variables that are needed are declared at the top, without values, in order for the parser to find the value fro those keys: 
```python
# ----------------------------------------------------------------------
# Declare needed config keys for script's functioning
# ----------------------------------------------------------------------
DB_VERSION = "v0.2.0"
SCOPES = []
SCHEMA_FILE = ""
GOOGLE_FORM_ID = ""
OAUTH_CLIENT_JSON = ""
TOKEN_CREATE_FORM = ""
DISCOVERY_DOC = ""
DEBUG = False
```

It then basically parses the schema and build the body of the request in a format that is compatible with Google Form API. 
It first creates the sections and adds questions to the form; then it applies the required section navigation logic to the created sections; it then renames the file and moves it the specified folder in Google Drive. 

**TODO:** it does not currently update the README with the link to the newly created form.

## Collecting the data
`collectResponses.py` again depends on `src/configParsing.py` and `src/authFlow_helpers.py`, and needs the variables specified at the top of the script (again without their values, the config parser takes care of filling them):
```python
# ----------------------------------------------------------------------
# Declare needed config keys for script's functioning
# ----------------------------------------------------------------------
SCOPES = []
SCHEMA_FILE = ""
GOOGLE_FORM_ID = ""
OAUTH_CLIENT_JSON = ""
TOKEN_COLLECT_RESPONSES = ""
DISCOVERY_DOC = ""
DEBUG = False
```

It first reads the responses from the form identified by `FORM_ID`; then, it loads the schema and uses the *question title* to match the questions to the `id` in the schema; it then grab the responses, and can now associate the responses to the schema's `id`, building a dictionary with `id` shorthands as keys and the response as value; finally, it writes out in `data/` a CSV with all the responses (one per row) as well as one JSON file for each response, named after the (sanitises) `deviceID` the user supplied while filling in the form. 

> [!CAUTION]
> The `id` field in the schema is lost when building the API request. 
> In order to associate questions pulled from the form (and their responses) to the schema, we need to match the *question title*. 
> This means that if the question title changes with different versions of the schema, this mapping would break!


# Lifecycle of the automated workflows
The automated workflows on Github actions are set up to only run on a schedule or when certain files are modified in the repo. 

## Tests
Various tests are defined in `.github/workflows/tests.yml`. This workflow get triggered when certain files are modified in the repo, mainly `hardware-db_schema.json`, the python scripts and `.env`. 

It runs three jobs: 
 - `validate_json`: to make sure that the modified schema satisfies expected format
 - `test_auth`: to ensure the authentication workflow succeeds
 - `test_config`: to assert that variables get assigned values in the expected precedence

If any fail, the other workflows will not get triggered. This is desirable, because failing these basic tests early makes it easier to troubleshoot issues and does not generate spurious forms. 

## Creating the Google Form from the schema
The workflow `.github/workflows/createForm.yml` triggers after a successful run of the Tests workflow. This means that it only triggers when Tests is triggered, and only if Tests succeeds. 

It reads access tokens from Github repo secrets, and then calls `createForm.py`. 

**TODO:** it does not currently update the README with the link to the newly created form.

## Collecting and parsing responses
The workflow `.github/workflows/collectResponses.py` starts on a schedule at 4am every day, and checks that the latest run of Tests was successful before running. 

It reads access tokens from Github repo secrets, and other variables, notably `FORM_ID`, from `.env`; if `FORM_ID` is assigned within the workflow itself, this takes precedence over the value in `.env` (i.e. for testing purposes). 

It then runs `collectResponses.py`, and pushes the CSV and JSON files to `data/` on the repo. 

> [!WARNING]
> Due to Github's design, `workflow_run` conditions only get triggered on the main branch, se thread [here](https://github.com/orgs/community/discussions/66512).

<!-- ### End of spoilers section -->
</details>


# Contacts
If you have questions please get in touch: [luca.pegoraro@wsl.ch](mailto:luca.pegoraro@wsl.ch)