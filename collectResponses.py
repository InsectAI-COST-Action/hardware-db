import json
import csv
from pathlib import Path
from datetime import datetime

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


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_schema_version(schema_path: str) -> str:
    """Extract schema version from the schema JSON file."""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema.get("_metadata", {}).get("schema_version", "1.0.0")
    except Exception as e:
        print(f"Warning: Could not retrieve schema version: {e}")
        return "1.0.0"


def write_csv_from_json_files(
    output_dir: Path,
    csv_file: Path,
    ordered_shortQ_to_titleQ: list[str],
) -> int:
    """Rebuild CSV from all JSON records currently present in data/."""
    def normalize_csv_cell(value) -> str:
        # Keep CSV one-record-per-line by flattening embedded line breaks in free-text fields.
        if value is None:
            return ""
        text = str(value)
        return " ".join(text.replace("\r\n", "\n").replace("\r", "\n").splitlines())

    rows_written = 0
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ordered_shortQ_to_titleQ)

        for json_path in sorted(output_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    item = json.load(jf)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: skipping {json_path.name}: {e}")
                continue

            row_values = [
                normalize_csv_cell(item.get(short, ""))
                for short in ordered_shortQ_to_titleQ
            ]
            writer.writerow(row_values)
            rows_written += 1

    return rows_written


# ----------------------------------------------------------------------
# Main fun: call APIs, parse responses, write outputs
# ----------------------------------------------------------------------
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

    for section in schema.get("sections", []):
        for q in section.get("questions", []):
            qid = q.get("id")
            title = q.get("title")
            if not qid or not title:
                continue
            shortQ_to_titleQ[qid] = title
            ordered_shortQ_to_titleQ.append(qid)


    ### Grab all responses (handle pagination explicitly)
    responses = []
    page_token = None
    while True:
        req = forms_service.forms().responses().list(
            formId=cfg["GOOGLE_FORM_ID"],
            pageToken=page_token,
        )
        page = req.execute()
        if cfg["DEBUG"]:
            print("responses page:")
            print(page)

        responses.extend(page.get("responses", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    count = len(responses)
    print(f"Found {count} responses")
    if count == 0:
        print("Warning: no form responses found in API response.")


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
    schema_version = get_schema_version(cfg["SCHEMA_FILE"])
    collection_date = datetime.utcnow().isoformat() + "Z"
    
    for row in parsed_rows:
        mapped = {short: "" for short in ordered_shortQ_to_titleQ}
        for qid, ans in row.items():
            short = idQ_to_shortQ.get(qid)
            if short:
                mapped[short] = ans
        
        # Add metadata to track schema version and collection context
        mapped["_metadata"] = {
            "schema_version": schema_version,
            "collected_from_form_id": cfg["GOOGLE_FORM_ID"],
            "collected_date": collection_date,
            "migrated_from_version": None
        }
        
        responses_shorthand.append(mapped)

    if cfg["DEBUG"]:
        print("responses_shorthand:")
        print(responses_shorthand)


    ### Export files in usable formats
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)


    ### Write individual JSON files for each response, with shorthand keys
    written = 0
    skipped = 0
    latest_by_filename = {}
    for item in responses_shorthand:
        device_name = item.get("device_name", "")
        filename = sanitize_filename(device_name)
        if not filename:
            filename = "unnamed_device"
        latest_by_filename[filename] = item

    for filename, item in latest_by_filename.items():
        json_path = output_dir / f"{filename}.json"

        # Only write if actual data changed (ignore _metadata when comparing)
        new_data = {k: v for k, v in item.items() if k != "_metadata"}
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as jf:
                existing = json.load(jf)
            existing_data = {k: v for k, v in existing.items() if k != "_metadata"}
            if existing_data == new_data:
                skipped += 1
                continue

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(item, jf, indent=2, ensure_ascii=False)
        written += 1

    print(f"JSON files written to {output_dir}: {written} updated, {skipped} unchanged")

    ### Always rebuild CSV from all JSON files currently in data/
    csv_file = output_dir / "_InsectAI_hardware-db.csv"
    rows_written = write_csv_from_json_files(output_dir, csv_file, ordered_shortQ_to_titleQ)
    print(f"CSV written to {csv_file} ({rows_written} rows)")

if __name__ == "__main__":
    main()
