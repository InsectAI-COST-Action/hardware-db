# Source - https://stackoverflow.com/a/54491882
# Posted by T.Nylund
# Retrieved 2026-02-10, License - CC BY-SA 4.0

import json
from jsonschema import validate

# Describe what kind of json you expect.
schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "info": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["title", "description"]
        },
        "settings": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "emailCollectionType": {"type": "string"}
            },
            "required": ["emailCollectionType"]
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {
                        "type": ["string", "null"]
                    },
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "required": {"type": "boolean"},
                                "type": {"type": "string"},
                                "paragraph": {"type": "boolean"},
                                "choiceType": {"type": "string"},
                                "low": {"type": "number"},
                                "high": {"type": "number"},
                                "options": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "logic": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "go_to": {"type": "string"}
                                        },
                                        "required": ["go_to"]
                                    }
                                }
                            },
                            "required": ["id", "title", "required", "type"]
                        }
                    }
                },
                "required": ["id", "title", "questions"]
            }
        }
    },
    "required": ["info", "settings", "sections"]
}

# Convert json to python object.
try: 
    with open ("../hardware-db_schema.json", "r") as f:
        my_json = json.load(f)
    try:
        validate(instance=my_json, schema=schema)
        print("Validation passed ✅")
    except Exception as e:
        print("Validation failed ❌:", e)   
except Exception as e:
    print("Failed to load, probably because of a malformed JSON:", e)
    my_json = None

# print for debug
print(my_json)

### ============================================== ###

# test case: pass ✅
my_json = {
    "info": {
        "title": "Example Form",
        "description": "Example description"
    },
    "settings": {
        "emailCollectionType": "If you'd like to :)"
    },
    "sections": [
        {
            "id": "section1",
            "title": "Section 1",
            "description": None,
            "questions": [
                {
                    "id": "question1",
                    "title": "Your name?",
                    "required": True,
                    "type": "text",
                    "paragraph": False
                }
            ]
        }
    ]
}

try:
    validate(instance=my_json, schema=schema)
    print("Validation passed ✅")
except Exception as e:
    print("Validation failed ❌:", e)


# test case: fail ❌
my_json = {
    "info": {
        "title": "Example Form",
        "description": "Example description"
    },
    "settings": {
        "emailCollectionType": False  # ❌ must be string
    },
    "sections": {  # ❌ must be a list
        "id": "section1",
        "title": "Section 1",
        "questions": [
            {
                "id": 123,  # ❌ must be string
                "title": "Your name?"
                # ❌ missing 'required'
                # ❌ missing 'type'
            }
        ]
    }
}

try:
    validate(instance=my_json, schema=schema)
    print("Validation passed ✅")
except Exception as e:
    print("Validation failed ❌:", e)
