# test_cfg.py
import sys
from configParsing import build_config

# ---- declare the keys you expect -----------------
SCOPES = []          # list → tells the parser "this is a list"
DEBUG = False        # bool → tells the parser "this is a bool"
SCHEMA_FILE = ""     # str  → tells the parser "this is a string"
# ------------------------------------------------

if __name__ == "__main__":
    # Extract variable names from command line BEFORE build_config parses args
    # This way we capture them before argparse removes them
    vars_to_print = []
    for arg in sys.argv[1:]:
        # Only treat uppercase names with underscores as variable names
        if arg.isupper() or '_' in arg and arg[0].isupper():
            vars_to_print.append(arg)
    
    # Remove variable names from sys.argv before calling build_config
    # This prevents argparse from complaining about unrecognized arguments
    sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg not in vars_to_print]
    
    cfg = build_config(globals())
    
    # If no variables were specified, print all
    if not vars_to_print:
        vars_to_print = list(cfg.keys())
    
    for k in vars_to_print:
        if k in cfg:
            v = cfg[k]
            print(f"{k:20} -> {repr(v)}   ({type(v).__name__})")
        else:
            print(f"{k:20} -> NOT FOUND", file=sys.stderr)