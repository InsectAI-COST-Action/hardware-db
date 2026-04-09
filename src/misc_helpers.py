import os
import re
import tempfile
import json
from collections import defaultdict

def sanitize_filename(name):
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w\-]", "", name)
    return name

def write_json_to_tmp(json_text: str) -> str:
    """Write a JSON string to a temporary file and return the file path."""
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="oauth_client_")
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    return tmp_path

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text.strip("_")

def transform_form(input_json):
    out = {
        "info": input_json["info"],
        "settings": input_json.get("settings", {}),
        "sections": []
    }

    current_section = {
        "id": "intro",
        "title": "Introduction",
        "description": None,
        "questions": []
    }

    seen_ids = defaultdict(int)

    def unique_id(base):
        seen_ids[base] += 1
        return base if seen_ids[base] == 1 else f"{base}_{seen_ids[base]}"

    for item in input_json["items"]:

        # Section break
        if "pageBreakItem" in item:
            if current_section["questions"]:
                out["sections"].append(current_section)

            base_id = slugify(item["title"])
            current_section = {
                "id": unique_id(base_id),
                "title": item["title"],
                "description": item.get("description"),
                "questions": []
            }
            continue

        # Question
        q = item["questionItem"]["question"]
        q_id = unique_id(slugify(item["title"]))

        question = {
            "id": q_id,
            "title": item["title"],
            "required": q.get("required", False)
        }

        if "textQuestion" in q:
            question["type"] = "text"
            question["paragraph"] = q["textQuestion"].get("paragraph", False)

        elif "choiceQuestion" in q:
            question["type"] = "choice"
            question["choiceType"] = q["choiceQuestion"]["type"]
            question["options"] = [
                opt["value"] for opt in q["choiceQuestion"]["options"]
            ]

        elif "scaleQuestion" in q:
            question["type"] = "scale"
            question["low"] = q["scaleQuestion"]["low"]
            question["high"] = q["scaleQuestion"]["high"]

        current_section["questions"].append(question)

    if current_section["questions"]:
        out["sections"].append(current_section)

    return out

with open("sanitised_form.json") as f:
    data = json.load(f)

structured = transform_form(data)

with open("structured_form.json", "w") as f:
    json.dump(structured, f, indent=2)
