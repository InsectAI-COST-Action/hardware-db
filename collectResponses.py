import json
import csv
import os
from pathlib import Path

from googleapiclient.discovery import build

from authFlow_helpers import resolve_oauth_path, make_creds
from configParsing import build_config
from misc_helpers import sanitize_filename


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


# ==================================================================
# Main fun: call APIs, parse responses, write outputs
# ===============================================================
def main():
    cfg = build_config(globals())
    
    oauth_path = resolve_oauth_path(cfg["OAUTH_CLIENT_JSON"])
    
    ### Make credentials
    creds = None
    creds = make_creds(
        OAUTH_CLIENT_JSON=oauth_path,
        TOKEN_FILE=cfg["TOKEN_COLLECT_RESPONSES"],
        SCOPES=cfg["SCOPES"],
    )

    ### Create services with stored credentials
    forms_service = build(
        "forms",
        "v1",
        credentials=creds,
        discoveryServiceUrl=cfg["DISCOVERY_DOC"],
        static_discovery=False,
    )


    ### Grab form details - we need this for the questionId's
    form_info = forms_service.forms().get(formId=cfg["GOOGLE_FORM_ID"]).execute()
    if cfg["DEBUG"]:
        print(form_info)

    form_info = form_info.get("items")
    if cfg["DEBUG"]:
        print("form_info:")
        print(form_info)

    # Make dictionary of question IDs (idQ) to question titles (titleQ)
    idQ_to_titleQ = {}
    for item in form_info:
        # print(item)
        if "questionItem" in item:
            idQ_to_titleQ[item["questionItem"]["question"]["questionId"]] = item["title"]

    if cfg["DEBUG"]:
        print("idQ_to_titleQ:")
        print(idQ_to_titleQ)


    ### Grab JSON schema, parse into handy dictionary,
    ### we need to match questionId to question title
    with open(cfg["SCHEMA_FILE"], "r", encoding="utf-8") as f:
        schema = json.load(f)

    # shortQ -> shorthand for question
    # titleQ -> actual question text
    shortQ_to_titleQ = {}
    ordered_shortQ_to_titleQ = []

    for section in schema["sections"]:
        for q in section["questions"]:
            qid = q["id"]
            title = q["title"]
            shortQ_to_titleQ[qid] = title
            ordered_shortQ_to_titleQ.append(qid)


    ### Grab the responses - this contains the answers proper
    responses = forms_service.forms().responses().list(formId=cfg["GOOGLE_FORM_ID"]).execute()
    if cfg["DEBUG"]:
        print("responses:")
        print(responses)

    responses = responses.get("responses", [])
    print(f"Found {len(responses)} responses")


    ### Parse responses into questionId to answer
    parsed_rows = []

    for response in responses:
        answer_map = {}

        answers = response.get("answers", {})

        for question_id in idQ_to_titleQ.keys():

            if question_id in answers:
                answer_obj = answers[question_id]

                # Handle different answer types
                if "textAnswers" in answer_obj:
                    values = [
                        a["value"] for a in answer_obj["textAnswers"]["answers"]
                    ]
                    answer_value = "; ".join(values)

                else:
                    answer_value = ""

            else:
                answer_value = ""

            answer_map[question_id] = answer_value

        parsed_rows.append(answer_map)

    ### Finally, match question IDs to question shorthands, and append answers,
    ### need to invert shorthand -> title to title -> shorthand
    title_to_short = {title: short for short, title in shortQ_to_titleQ.items()}

    # Map Google question IDs -> shorthand (when title matches)
    idQ_to_shortQ = {}
    for qid, title in idQ_to_titleQ.items():
        short = title_to_short.get(title)
        if short:
            idQ_to_shortQ[qid] = short

    # Build list of responses where keys are shorthand (preserve schema order)
    responses_shorthand = []
    for row in parsed_rows:
        mapped = {short: "" for short in ordered_shortQ_to_titleQ}
        for qid, ans in row.items():
            short = idQ_to_shortQ.get(qid)
            if short:
                mapped[short] = ans
        responses_shorthand.append(mapped)

    if cfg["DEBUG"]:
        print("responses_shorthand:")
        print(responses_shorthand)


    ### Export files in usable formats
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)


    ### Write CSV with shorthand keys as headers, and answers as rows
    csv_file = output_dir / "form_responses.csv"

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        header = list(responses_shorthand[0].keys())
        writer.writerow(header)

        for item in responses_shorthand:
            writer.writerow(list(item.values()))

    print(f"CSV written to {csv_file}")


    ### Write individual JSON files for each response, with shorthand keys
    for item in responses_shorthand:

        device_name = item.get("device_name")
        filename = sanitize_filename(device_name)

        json_path = output_dir / f"{filename}.json"

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(item, jf, indent=2, ensure_ascii=False)

    print(f"JSON files written to {output_dir}")
    
if __name__ == "__main__":
    main()