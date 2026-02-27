# Source - https://stackoverflow.com/a/54491882
# Posted by T.Nylund
# Retrieved 2026-02-10, License - CC BY-SA 4.0

import json
from jsonschema import validate

# Import validation schema.
# See http://json-schema.org/draft-07/schema# for syntax
with open("validation_schema.json", "r") as f: 
    schema = json.load(f)

# Try to load target JSON, then validate against schema.
# ⚠️ if validation fails, only the first error is printed.
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

# # Pretty print for debug
# print(json.dumps(my_json, indent=2))


### ============================================== ###
# Below some examples that should pass and fail validation 
# to test the schema itself.


# # Test case: pass ✅
# my_json = {
#     "info": {
#         "title": "Example Form",
#         "description": "Example description"
#     },
#     "settings": {
#         "emailCollectionType": "If you'd like to :)"
#     },
#     "sections": [
#         {
#             "id": "section1",
#             "title": "Section 1",
#             "description": None,
#             "questions": [
#                 {
#                     "id": "question1",
#                     "title": "Your name?",
#                     "required": True,
#                     "type": "text",
#                     "paragraph": False
#                 }
#             ]
#         }
#     ]
# }

# try:
#     validate(instance=my_json, schema=schema)
#     print("Validation passed ✅")
# except Exception as e:
#     print("Validation failed ❌:", e)


# # Test case: fail ❌
# my_json = {
#     "info": {
#         "title": "Example Form",
#         "description": "Example description"
#     },
#     "settings": {
#         "emailCollectionType": False  # ❌ must be string
#     },
#     "sections": {  # ❌ must be a list
#         "id": "section1",
#         "title": "Section 1",
#         "questions": [
#             {
#                 "id": 123,  # ❌ must be string
#                 "title": "Your name?"
#                 # ❌ missing 'required'
#                 # ❌ missing 'type'
#             }
#         ]
#     }
# }

# try:
#     validate(instance=my_json, schema=schema)
#     print("Validation passed ✅")
# except Exception as e:
#     print("Validation failed ❌:", e)
