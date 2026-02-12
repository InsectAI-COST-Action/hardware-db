# Redesigning approach dev notes

The general idea is to implement this workflow: 
```
DATABASE STRUCTURE JSON --- createForms.py ---> FULL FORM
FULL FORM --- collectResponses.py ---> responses (JSON, CSV)
```

**Re-implementation TODO list:**
- [x] Proof of concept JSON to Google Form
- [x] Transfer over actual questions into JSON format: 
    - [x] Basic form: [Form link](https://docs.google.com/forms/d/1mXaEkw1lydgeE5Ld0X5j2Xp82ABDgnQeQ79CvEJi_UQ/edit) or in `json_body.json` + `json_form.json` if generated from that. *apparently this is the same as the full version now?*
    - [x] Full form: [Form link](https://docs.google.com/forms/d/1k7RsEdOJrLW6ZDwOTHNdgDH2VSYWETfCI-1HyznB0m8/edit) or in `json_body.json` + `json_form.json` if generated from that. 
- [x] Re-hash the form so that the basic questions line up with Wildlab's [The Inventory](https://wildlabs.net/inventory). 
  - [x] Add further branching in the logic for basic VS full form. 
- [x] Get some dummy answers in the form to test.
- [x] Implement collecting answers and parsing into human-readable JSON
- [x] Add schema's validation for valid JSON
- [ ] ~~Change from OAuth token-based authentication to service account-based authentication (i.e. like for ACCESS website)~~ - this is not supported by Google API
- [ ] Develop CI/CD workflow on Github

*Extras*
- [ ] Will need to come up with a sensible versioning/tagging system for JSON database ontology 
- [ ] Make basic frontend for visualising answers (static website w/ GitHub pages?)
- [ ] Other tests?


**Outstanding issues:**
- [ ] Scope of `hardware-db`: how to align with "Technology type" in Wildlabs? Do we only take camera-based tech???
- [ ] Collating answers
  - [ ] how to track response spreadsheet when form is re-generated at every JSON schema update?
  - [ ] what about attached pictures?
- [ ] Updating existing record
  - [ ] How to uniquely identify each entry? Ask user for unique name (but then how to check?)
  - [ ] How to retrieve info and pre-populate form with it? 
  - [ ] We might also just ask them to contact us and/or resubmit... 

## Proof of concept
Proof of concept with `createForm.py` and JSON-based questions successful. We can even do simple logic navigation within the form. 

The way this works currently is that it creates a new form with every rerun; *does not* append questions to existing form. The idea is that we could trigger re-building of the form upon changes to the underlying JSON ontology. For that, will need to implement a versioning or tagging system to keep track of which form is generated from which ontology. 

## Migrating to JSON-based schema
I figures it would be easier to start from the full form and modify its structure to produce JSON for the database schema. 

`extractingQuestions_temp.py` grabs the info from the existing full form, and additionally removes unnecessary info like questionsId and similar (fun `sanitise_form`), since they will be lost anyway during form creation. 
Also added section and questions syntax to improves readability and facilitates modification down the line. These map to Google Forms API's terms like so: 

| JSON schema    | Google Forms API   |
| -------------- | ------------------ |
| `form.title`   | `info.title`       |
| `sections[]`   | `pageBreakItem`    |
| `questions[]`  | `questionItem`     |
| Question order | insertion order    |
| Section order  | insertion order    |
| Symbolic `id`  | not sent to Google |

Importantly, the `id` field is what I will use to collect the answers, as a shorthand for the question. It needs to be unique. 

The order the questions will appear in the form is determined by their order within the JSON, nested within `section[]`. 

The general syntax is as follows: 
 - There's an `info` block, that contains general details for form. 
 - This is followed by `settings`, currently only manages whether sign-in is required. 
 - Then there's the `section` block, that takes a unique `id` and other details
 - Nested within `section`, there's `questions`, that itself takes a unique `id` and the question, its description and type as well as allowed options (for some types). 

Within-block syntax follows quite closely Google Forms API's syntax. 
Example JSON schema below:
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
}
```
Trying to add logic handling from the JSON schema, using unique `id`s as anchors. 

Adding `logic` block to JSON, *only choice questions supported*, that has a `got_to` key that maps to API actions: 

| Value          | API equivalent                        | Meaning              |
| -------------- | ------------------------------------- | -------------------- |
| `"section_id"` | `goToSectionId: "<pageBreak itemId>"` | Jump to that section |
| `"next"`       | `goToAction: "NEXT_SECTION"`          | Go to next section   |
| `"submit"`     | `goToAction: "SUBMIT_FORM"`           | Submit form          |

The logic for the new parser (still names `createForm.py`) is that it first creates all sections, then adds the questions under the appropriate section, then adds logic (i.e. if q1 "yes" then go to sec2, if "no" go to sec3). 
It's necessary to do two passes of the form, because the API only allows redirection to a specific sectionID, and these are non-meaningful (i.e. create on the fly), so you need to query the form you just created to retrieve these ids and then apply the logic to them. 
Now parses descriptions of sections as well (and not just the overall form description at the top).

## Aligning with Wildlab's The Inventory
To find out what are the required fields, and what values they take, I typed in *by hand* all the info in their submission form... It is in `WildlabsInventory_schema.json`, formatted as JSON. 
Each top-level item correspond to a page/view, that would be a section in a Google Form. 
Data types are guessed, and should be fairly self-explanatory. 

### Changing the required fields in the schema
As it is, the only `"required": true` items in the schema are (some details omitted): 
```json
{
{
    "questions": [
        {
            "id": "have_deviceID",
            "title": "Do you already have a deviceID for this hardware?",
            "required": true,
            "type": "choice",
            "choiceType": "RADIO",
            "options": [
                "Yes",
                "No"
            ],
            "logic": {
                "Yes": {
                    "go_to": "new_device_version"
                },
                "No": {
                    "go_to": "contributor_details"
                }
            }
        },
        {
            "id": "previous_deviceID",
            "title": "Previous deviceID",
            "required": true,
            "type": "text",
            "paragraph": false
        },
        {
            "id": "device_creator_email",
            "title": "Device creator email(s)",
            "required": true,
            "type": "text",
            "paragraph": false
        },
        {
            "id": "contributor_name",
            "title": "Contributor name",
            "required": true,
            "type": "text",
            "paragraph": false
        },
        {
            "id": "contributor_email",
            "title": "Contributor email",
            "required": true,
            "type": "text",
            "paragraph": false
        },
        {
            "id": "maintainer_name",
            "title": "Maintainer name",
            "required": true,
            "type": "text",
            "paragraph": false
        },
        {
            "id": "maintainer_email",
            "title": "Maintainer email",
            "required": true,
            "type": "text",
            "paragraph": false
        }
    ]
}
``` 

In my opinion, it doesn't make a lot of sense to have this many names & contact details mandatory, and not make mandatory the device name or description. 

What I suggest to be mandatory, also to better align with Wildlabs's schema, is: 
```
Replace all "device creator", "contributor" and "maintainer" names + email combo with "contact" name +  email. 
The other specifications for other roles can be in the full form, non-mandatory. 

Make "device_name" and "device_description" mandatory. 
```

So the only mandatory fields in our basic form would be (and their correspondence in Wildlab's Inventory):

| InsectAI `hardware-db` | Wildlab's Inventory             |
| ---------------------- | ------------------------------- |
| `contact_name`         | `Name` (collected via sign-in)  |
| `contact_email`        | `Email` (collected via sign-in) |
| `device_name`          | `Product_name`                  |
| `device_description`   | `Overview`                      |

Keeping the old schema to rebuild the full form as Graham envisioned it as `hardware-db_schema_OLD_fFullForm.json`. 

## Collecting and parsing responses
The script `collectResponses.py` queries the existing Form via its ID, and gets the responses. 

There is, as far as I can see, no way to trigger the creation of a Google Spreadsheet via the API, in practice there is no analogue to the "Response" > "Link to Sheets" button in the Forms GUI. 

This means that we have to find some other way of integrating responses from different versions of the form, we cannot do it via a spreadsheet, at least there isn't a documented way of doing so. 

Focussing now on parsing the responses in separate JSON files (one-per-response) and one unified CSV (with all responses). 

## Changing authentication method
Let's now work on changing the OAuth2-based method (good for personal accounts) to a service account authentication method (good for machine-to-machine auth, automated workflows). 

Borrowing from [ACCESS-2026](https://github.com/darsa-group/ACCESS-2026/tree/source?tab=readme-ov-file#secrets-management), let;s create a new token for my @wsl.ch Google account.
As an aside, I had to enable 2FA to be able to use Google Cloud Console. 

We need to generate a service account authentication token. 

`GOOGLE_SERVICE_JSON_KEY`: this is the JSON content of a Google Cloud service account key. To get it:
  - Go to the [Google Cloud Console](https://console.cloud.google.com/).
  - Create or select a project - I selected the pre-existing `InsectAI-hardwareDB-backend`
  - Enable the Google Forms API. 
  - Create a service account (IAM & Admin > Service Accounts).
  - Generate a JSON key for the service account
  - Copy the JSON content and set it as the env var (e.g., in a .secret file or system env).

Ok, so I managed to set up the authentication workflow with some secrets management locally. But the form is not being created, probably because the service account cannot access files in my account's Drive (I read somewhere that service accounts can have their own Drive space, but I didn't activate it and in any case it would not be accessible to anyone but the service account). 

I will now try to create a shared Drive folder from my own Drive and share it with the service account... 

Need to create the form first as a regular Google Drive file (with appropriate MIME type), then update the form with questions and stuff. 

⛔ Turns out, I cannot use a service account to interact with a personal Google Drive, this is a limitation that google imposes... 

Will need to find another way to not have to re-authenticate frequently with OAuth2 tokens on Github. 

## Developing CD/CI pipeline on github
The first step is making sure that the authentication workflow can work on GitHub Actions. 

Adding a simple test `test/testAuth.py` to verify the ability to write files etc to Google Drive with an OAuth2 token. 


> [!TIP]
> Don't forget to look at https://github.com/rhine3/bioacoustics-software for inspiration about the workflow!


<details>   <!-- this is to begin the "spoiler section" -->
  <summary><h2>Original README contents</h2></summary>

# [OLD] Insect AI Hardware Database

<p align="center">
<img src="./assets/Hardware-dtb-image.png" width="540"/>
</p>

## Data submission pipeline for documenting of Insect AI hardware

This repository contains the following:
- Link to a Google Master spreadsheet - the schema defining accepted fields, validation criteria and metadata for Google form generation.
- Link to the most up-to-date Google form(s) - the method of data input by contributors to the database entries
- Script for generating Google forms from the Master spreadsheet
- Table showcasing basic details of hardware submitted by contributors so far

## Introduction

### Scope

#### Script

`debugScript.py` is a Python script which converts the Master google spreadsheet of hardware (the ground truth for the database) into a JSON file which in turn is used to produce a google form. The generated Google Form requests details from hardware developers, modifiers and users and is the entry point for submission to the hardware database. Google sheet and Google form handling is achieved through their respective Google API's which are called in the script. Currently when running the script for the first time you will be prompted to log in to a google account to generate a token that will allow usage of the API's.

#### Master spreadsheet

This is the [Master Sheet](https://docs.google.com/spreadsheets/d/1DClwffVrkrwH0G5nuCVCJVVoLLdueuqHdJ_VXWPc_Pg/edit?gid=0#gid=0) that contains the form generation metadata. 

#### Submission forms

This is the [Full Form](https://docs.google.com/forms/d/19htB7BIDoh3ngRtvgURIyCrT1Cir_ScP4lWVnZ-ftHc/edit) for detailed entry submission.

</details>   <!-- this is to end the "spoiler section" -->

> [!CAUTION]
> If, when running any of the scripts, you get an error like: 
>``` python
>google.auth.exceptions.RefreshError: ('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})
>```
>It just means that the token is expired and re-authentication workflow is stuck. Simply remove the file `token.json` that gets saved in the same dir as the script and authenticate again. 

# ToDos
- [ ] Refactor big script into helper functions script, and various targeted script
    - [ ] Bonus: add argparse to add exports, dry run and verbosity levels. 
    - [x] move export into dedicated folder
- [ ] Add github pages automation
    - [ ] need to investigate the best way to store credentials
- [ ] Create (or do we have one already?)  InsectAI Gmail account that an own the various spreadsheets, forms and eventually GDrive with the uploaded pictures. 
- [ ] Restructure the README so that it has a quickstart section for contributors and link to the data at the top, explanation and maintenance notes after. 

*Only after discussing with Graham & others:*
- [ ] Change to new workflow with JSON-based database ontology that propagates in Google forms. 
- [ ] Prepare exports in an easily accessible format: one JSON file per device (+ picture) or one single CSV dump for all devices (+link to pics)?

<details>   <!-- this is to begin the "spoiler section" -->
  <summary><h2>Luca's dev notes</h2></summary>

### Authorising Google API and running locally

To test if the script compiles correctly, I need to authorise locally the script to access the Master Sheet and (?) the form. 

Making a copy into my own Google account (luca.pegoraro@wsl.ch) of the Master Sheet. 

The Google sheets ID and Google form ID are the alphanumeric string in the URL, just copy those. 

Getting the API token required for OAuth2 authentication. 
On the luca.pegoraro@wsl.ch Google account, enable the relevant APIs: Google Sheets, Google Forms and Google Drive. 
Then, create Oauth consent screen for your app (I called it "InsectAI hardware-db"). 

Under Google Auth Platform > Clients > Create client you can finally create the OAuth client ID that you need to authorize a desktop app to access private data in sheets, forms and so on. Here you can finally download the JSON file you need. 

*[credentials edited out for privacy]*

Can you rename the JSON you download? - Yep, sure looks like it. 

You also need to add Test users to the app if it's in testing mode. I've added myself and Graham's google accounts. 

Now running the authentication workflow (`debugScript.py:47-54`)  will open a webpage, and ask for authorization to access personal data from your google account. 

It writes a token.json file with the specified scopes. 

### What does what

`debugScript.py` for now contains everything, from form creation and update to exports. Will need to separate out in different scripts: 
 - helper functions related to Google API (maybe also config variables reading) 
 -  form creation and update (maybe both response and feedback form together)
 -  reading and exporting from responses 

`oauth_client-WSL_laptop.json` contains the credentials for the google API, these are used to request or refresh the token that allows time-limited access to the data. 

`token.json` this is the token that gets refreshed every time you request data. 

`json_body.json`, `json_existing.json`, `json_form.json` and `json_info.json` are all exports of the script that contain almost the same information, namely the form headings, questions and allowed answers. Maybe they serve some purpose for debugging but will need to consolidate them. 

`form_responses.csv` and `form_responses.json` are new exports I made that grab the responses to the form and save them. They still have questions IDs and not the actual text of the question. 

## New workflow idea

After delving into the nuts and bolts of the current workflow, I think I have another idea of how to manage it. 

The current workflow is: 
```
MASTER SPREADHSEET --- debugScript.py ---> FULL FORM
FULL FORM --- debugScript.py ---> JSON exports
FULL FORM --- debugScript.py (added funs) ---> responses (JSON & CSV)
```

I feel like defining questions and values and all that in a spreadhseet is too brittle, and does not allow for easy tracking. Realistically, after the initial phase (i.e. now), the database structure will not need sweeping changes very frequently. 
I would much prefer to see a text based, versioned structure, that can be used to create the form. 

Below a revised workflow proposition: 
```
(NEW) DATABASE STRUCTURE JSON --- (NEW) createForms.py ---> FULL FORM, SIMPLE FORM
FULL FORM, SIMPLE FORM --- (NEW) collectResponses.py ---> responses (JSON, CSV)
```

When modification to the DB structure are needed, these can be made at the point DATABASE STRUCTURE JSON and propagate to the rest of the pipeline from there. 
The frontend can then be served using the CSV or JSON exports as data sources. 

</details>   <!-- this is to end the "spoiler section" -->