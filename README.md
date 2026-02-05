⚠ Luca: I used this branch to modify the code run locally on my machine, as wella s using Google Sheets and Forms that I owned, to test transferability.  No further fetaure development beyond should be pushed here. ⚠

# Redesigning approach dev notes

The general idea is to implement this workflow: 
```
DATABASE STRUCTURE JSON --- createForms.py ---> FULL FORM
FULL FORM --- collectResponses.py ---> responses (JSON, CSV)
```


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