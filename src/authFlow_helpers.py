import os
import io
import json
import tempfile

# ----------------------------------------------------------------------
# Helper: Turn the secret (path **or** raw JSON) into a real file path
# ----------------------------------------------------------------------
def _write_json_to_tmp(json_text: str) -> str:
    """Write a JSON string to a temporary file and return the file path."""
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="oauth_client_")
    os.close(fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(json_text)
    return tmp_path


def resolve_oauth_path() -> str:
    """
    Return a filesystem path that points to a valid OAuth client JSON file.

    Preference order:
      - OAUTH_CLIENT_JSON env var that already points to an existing file.
      - OAUTH_CLIENT_JSON env var that contains the raw JSON payload.
      - .secrets file with a line like: OAUTH_CLIENT_JSON=/full/path/to/client.json
    Raises:
      FileNotFoundError if nothing usable is found.
    """
    # ----- Existing file? -----
    env_val = os.getenv("OAUTH_CLIENT_JSON")
    if env_val:
        if os.path.isfile(env_val):
            # It's already a path – use it directly.
            return env_val

        # Not a file → assume it is the raw JSON text.
        try:
            json.loads(env_val)          # sanity‑check that it parses
        except Exception as exc:
            raise FileNotFoundError(
                "OAUTH_CLIENT_JSON is set but is neither a valid file nor valid JSON."
            ) from exc
        # Write the JSON to a temp file and hand that path back.
        return _write_json_to_tmp(env_val)

    # ----- .secrets fallback (local dev) -----
    secrets_file = ".secrets"
    if os.path.isfile(secrets_file):
        with open(secrets_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("OAUTH_CLIENT_JSON="):
                    candidate = line.split("=", 1)[1].strip()
                    if os.path.isfile(candidate):
                        return candidate
                    raise FileNotFoundError(
                        f"The path '{candidate}' referenced in .secrets does not exist."
                    )

    # ----- Nothing worked -----
    raise FileNotFoundError(
        "Unable to locate OAuth client JSON. Either set the OAUTH_CLIENT_JSON "
        "environment variable (to a path or to the raw JSON) or create a "
        ".secrets file containing a line like:\n"
        "OAUTH_CLIENT_JSON=/full/path/to/OAuth_client.json"
    )
