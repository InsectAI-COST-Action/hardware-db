# test_cfg.py
from configParsing import build_config

# ---- declare the keys you expect -----------------
SCOPES = []          # list → tells the parser “this is a list”
DEBUG = False        # bool → tells the parser “this is a bool”
SCHEMA_FILE = ""     # str  → tells the parser “this is a string”
# ------------------------------------------------

if __name__ == "__main__":
    cfg = build_config(globals())
    for k, v in cfg.items():
        print(f"{k:20} -> {repr(v)}   ({type(v).__name__})")