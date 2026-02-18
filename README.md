# Insect AI Hardware Database

<p align="center">
**🚧 Under construction! 🚧**
<img src="./assets/Hardware-dtb-image.png" width="540"/>
</p>

For progress see [Development notes](DevNotes), [TODO](TODO) and [CHANGELOG](CHANGELOG).

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
