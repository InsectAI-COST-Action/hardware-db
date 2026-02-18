import os
import re
import tempfile

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