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
    except Exception as e:
        print("Validation failed:", e)
    
except Exception as e:
    print("Failed to load, probably because of a malformed JSON:", e)
    my_json = None

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
    "sections": [{
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
            }}}]
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
