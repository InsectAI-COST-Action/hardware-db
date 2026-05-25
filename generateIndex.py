"""
generateIndex.py

Reads all JSON files in data/ and writes:
  - docs/devices_index.json  (device list for the GitHub Pages landing page)
  - docs/form_config.json    (form URL; preserves entry_ids set by createForm.py)

Requires no third-party dependencies — stdlib only.
GOOGLE_FORM_ID is resolved from (in order):
  1. GOOGLE_FORM_ID environment variable
  2. GOOGLE_FORM_ID= line in .env file
  3. form_id already present in docs/form_config.json
"""

import json
import os
from pathlib import Path


def read_dotenv(env_file: str = ".env") -> dict:
    """Parse a .env file into a plain dict (no external library needed)."""
    env_path = Path(env_file)
    result = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def main():
    data_dir = Path("data")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Build device index from every JSON file in data/
    # ------------------------------------------------------------------
    index_entries = []
    for json_path in sorted(data_dir.glob("*.json")):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                item = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {json_path.name}: {e}")
            continue

        device_name = item.get("device_name", "")
        filename = json_path.stem   # already sanitised at write time
        meta = item.get("_metadata", {})
        index_entries.append({
            "filename": filename,
            "device_name": device_name,
            "institution_name": item.get("institution_name", ""),
            "contact_name": item.get("contact_name", ""),
            "contact_email": item.get("contact_email", ""),
            "contributor_name": item.get("contributor_name", ""),
            "contributor_email": item.get("contributor_email", ""),
            "maintainer_name": item.get("maintainer_name", ""),
            "maintainer_email": item.get("maintainer_email", ""),
            "device_creator": item.get("device_creator", ""),
            "device_creator_email": item.get("device_creator_email", ""),
            "device_description": item.get("device_description", ""),
            "github_link": item.get("github_link", ""),
            "documentation_link": item.get("documentation_link", ""),
            "collected_date": meta.get("collected_date", ""),
            "schema_version": meta.get("schema_version", ""),
        })

    index_path = docs_dir / "devices_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_entries, f, indent=2, ensure_ascii=False)
    print(f"Device index written to {index_path} ({len(index_entries)} entries)")

    # ------------------------------------------------------------------
    # Update docs/form_config.json with the current form URL.
    # Preserves entry_ids that may have been set by createForm.py.
    # ------------------------------------------------------------------
    form_config_path = docs_dir / "form_config.json"
    existing_config = {}
    if form_config_path.exists():
        try:
            with open(form_config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    form_id = (
        os.environ.get("GOOGLE_FORM_ID")
        or read_dotenv().get("GOOGLE_FORM_ID")
        or existing_config.get("form_id")
    )

    if form_id:
        existing_config["form_id"] = form_id
        existing_config["form_url"] = (
            f"https://docs.google.com/forms/d/{form_id}/viewform"
        )
        if "entry_ids" not in existing_config:
            existing_config["entry_ids"] = {}
        with open(form_config_path, "w", encoding="utf-8") as f:
            json.dump(existing_config, f, indent=2)
        print(f"Form config updated at {form_config_path}")
    else:
        print("Warning: GOOGLE_FORM_ID not found; form_config.json not updated.")


if __name__ == "__main__":
    main()
