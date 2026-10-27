import unittest
import json
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from createForm import build_template_item_requests, normalize_form_id
from collectResponses import extract_answer_value


class TemplateFormTests(unittest.TestCase):
    def test_builds_schema_order_around_upload_slots(self):
        schema = {
            "sections": [
                {
                    "id": "first",
                    "title": "First",
                    "questions": [
                        {
                            "id": "upload_a",
                            "title": "Upload images",
                            "description": "Use JPG or PNG",
                            "required": False,
                            "type": "file_upload",
                        },
                        {
                            "id": "notes",
                            "title": "Notes",
                            "required": False,
                            "type": "text",
                        },
                    ],
                },
                {
                    "id": "last",
                    "title": "Last",
                    "questions": [
                        {
                            "id": "upload_b",
                            "title": "More images",
                            "required": True,
                            "type": "file_upload",
                        }
                    ],
                },
            ]
        }
        template_items = [
            {
                "itemId": "upload-item-a",
                "questionItem": {"question": {"fileUploadQuestion": {}}},
            },
            {
                "itemId": "upload-item-b",
                "questionItem": {"question": {"fileUploadQuestion": {}}},
            },
        ]

        requests, create_refs, item_ids, item_locations = (
            build_template_item_requests(schema, template_items)
        )

        self.assertEqual(
            [next(iter(request)) for request in requests],
            ["createItem", "createItem", "createItem"],
        )
        self.assertEqual(item_ids[("question", "upload_a")], "upload-item-a")
        self.assertEqual(item_locations[("question", "upload_a")], 1)
        self.assertEqual(item_ids[("question", "upload_b")], "upload-item-b")
        self.assertEqual(item_locations[("question", "upload_b")], 4)
        self.assertEqual(create_refs[("section", "first")], 0)

    def test_rejects_template_upload_count_mismatch(self):
        with self.assertRaisesRegex(ValueError, "schema declares 1"):
            build_template_item_requests(
                {
                    "sections": [
                        {
                            "id": "images",
                            "title": "Images",
                            "questions": [
                                {
                                    "id": "images",
                                    "title": "Images",
                                    "required": False,
                                    "type": "file_upload",
                                }
                            ],
                        }
                    ]
                },
                [],
            )

    def test_normalizes_form_url_or_id(self):
        self.assertEqual(
            normalize_form_id("https://docs.google.com/forms/d/abc123/edit"),
            "abc123",
        )
        self.assertEqual(normalize_form_id("abc123"), "abc123")

    def test_extracts_uploaded_file_metadata(self):
        result = extract_answer_value({
            "fileUploadAnswers": {
                "answers": [
                    {
                        "fileId": "drive-file-1",
                        "fileName": "device.jpg",
                        "mimeType": "image/jpeg",
                    }
                ]
            }
        })

        self.assertEqual(
            result,
            [{
                "file_id": "drive-file-1",
                "file_name": "device.jpg",
                "mime_type": "image/jpeg",
            }],
        )

    def test_validation_schema_accepts_file_upload_type(self):
        validation_schema_path = (
            Path(__file__).resolve().parent / "validation_schema.json"
        )
        validation_schema = json.loads(
            validation_schema_path.read_text(encoding="utf-8")
        )
        question_type_schema = (
            validation_schema["properties"]["sections"]["items"]["properties"]
            ["questions"]["items"]["properties"]["type"]
        )

        jsonschema.validate("file_upload", question_type_schema)


if __name__ == "__main__":
    unittest.main()
