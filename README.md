<h1> Insect AI Hardware Database </h1>

<img src="https://raw.githubusercontent.com/InsectAI-COST-Action/hardware-db/refs/heads/main/Hardware-dtb-image.png?token=GHSAT0AAAAAADPVNV2W44XLNXQH4JT34DI62JR32EA" width="540">

<h2> Data submission pipeline for documentating of Insect AI hardware </h2>

This repository contains the following:
- Link to a Google Master spreadsheet - the schema defining accepted fields, validation criteria and metadata for Google form generation.
- Link to the most up-to-date Google form(s) - the method of data input by contributors to the database entries
- Script for generating Google forms from the Master spreadsheet
- Table showcasing basic details of hardware submitted by contributors so far

<h3> Introduction  </h3>


<h3> Scope </h3>

<h4> Script </h4>

`debugScript.py` is a Python script which converts the Master google spreadsheet of hardware (the ground truth for the database) into a JSON file which in turn is used to produce a google form. The generated Google Form requests details from hardware developers, modifiers and users and is the entry point for submission to the hardware database. Google sheet and Google form handling is achieved through their respective Google API's which are called in the script. Currently when running the script for the first time you will be prompted to log in to a google account to generate a token that will allow usage of the API's.

<h4> Master spreadsheet </h4>

This is the [Master Sheet](https://docs.google.com/spreadsheets/d/1DClwffVrkrwH0G5nuCVCJVVoLLdueuqHdJ_VXWPc_Pg/edit?gid=0#gid=0) that contains the form generation metadata. 

<h4> Submission forms </h4>

This is the [Full Form](https://docs.google.com/forms/d/19htB7BIDoh3ngRtvgURIyCrT1Cir_ScP4lWVnZ-ftHc/edit) for detailed entry submission.

