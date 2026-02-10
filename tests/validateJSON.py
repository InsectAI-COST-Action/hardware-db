# Source - https://stackoverflow.com/a/54491882
# Posted by T.Nylund
# Retrieved 2026-02-10, License - CC BY-SA 4.0

import json
from jsonschema import validate

# Describe what kind of json you expect.
schema = {
    "info": {
        "title": {"type": "string"},
        "description": {"type": "string"},
    },
    "settings": {
        "emailCollectionType": {"type": "string"}
        },
    "sections": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "questions": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "required": {"type": "boolean"},
            "type": {"type": "string"},
            "paragraph": {"type": "boolean"},
            "options": [
                {"type": "string"}
            ],
            "logic": {
                "Yes": {"go_to": {"type": "string"}},
                "No": {"go_to": {"type": "string"}}
            }
        }
    }
}

# Convert json to python object.
with open ("../hardware-db_schema.json", "r") as f:
    my_json = json.load(f)

# Validate will raise exception if given json is not what is described in schema.
validate(instance=my_json, schema=schema)

# print for debug
print(my_json)

### ============================================== ###

# test case: pass ✅
my_json = {
    "info": {
        "title": "Example Form",
        "description": "This is an example form."
    },
    "settings": {
        "emailCollectionType": "optional"
    },
    "sections": {
        "id": "section1",
        "title": "Section 1",
        "description": "This is the first section.",
        "questions": {
            "id": "question1",
            "title": "What is your name?",
            "required": True,
            "type": "text",
            "paragraph": False,
            "options": [],
            "logic": {
                "Yes": {"go_to": "section2"},
                "No": {"go_to": "section3"}
            }
        }
    }
}

try:
    validate(instance=my_json, schema=schema)
except Exception as e:
    print("Validation failed:", e)


# test case: fail ❌
my_json = {
    "info": {
        "title": "Example Form",
        "description": "This is an example form."
    },
    "settings": {
        "emailCollectionType": False
    },
    "sections": {
        "id": "section1",
        "title": "Section 1",
        "description": "This is the first section.",
        "questions": {
            "id": 47,
            "title": "What is your name?",
            # missing required field 'required'
            # missing required field 'type'
            # missing required field 'paragraph'
            # missing required field 'options'
            # missing required field 'logic'
        }
    }
}

try:
    validate(instance=my_json, schema=schema)
except Exception as e:
    print("Validation failed:", e)
