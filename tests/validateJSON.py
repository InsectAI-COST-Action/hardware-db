# Source - https://stackoverflow.com/a/54491882
# Posted by T.Nylund
# Retrieved 2026-02-10, License - CC BY-SA 4.0

import json
from jsonschema import validate

# Describe what kind of json you expect.
schema = {
    "type" : "object",
    "properties" : {
        "description" : {"type" : "string"},
        "status" : {"type" : "boolean"},
        "value_a" : {"type" : "number"},
        "value_b" : {"type" : "number"},
    },
}

# Convert json to python object.
my_json = json.loads('{"description": "Hello world!", "status": true, "value_a": 1, "value_b": 3.14}')

# Validate will raise exception if given json is not
# what is described in schema.
validate(instance=my_json, schema=schema)

# print for debug
print(my_json)
