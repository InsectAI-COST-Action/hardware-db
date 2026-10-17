import unittest

from src.dataMigrations import SchemaMigration


class ValueMapFallbackTests(unittest.TestCase):
    def apply_value_map(self, value, transform):
        migration = SchemaMigration(
            "1.0.0",
            "1.1.0",
            {
                "drops": [],
                "adds": [],
                "renames": [],
                "transforms": [transform],
            },
        )
        return migration.apply_to_response({"field": value})["field"]

    def test_single_value_preserve_fallback_keeps_unmapped_value(self):
        result = self.apply_value_map(
            "legacy value",
            {
                "type": "value_map",
                "question_id": "field",
                "value_map": {"known": "mapped"},
                "fallback_value": "preserve",
            },
        )

        self.assertEqual(result, "legacy value")

    def test_single_value_preserve_fallback_does_not_override_mapping(self):
        result = self.apply_value_map(
            "known",
            {
                "type": "value_map",
                "question_id": "field",
                "value_map": {"known": "mapped"},
                "fallback_value": "preserve",
            },
        )

        self.assertEqual(result, "mapped")

    def test_single_value_literal_fallback_still_replaces_unmapped_value(self):
        result = self.apply_value_map(
            "legacy value",
            {
                "type": "value_map",
                "question_id": "field",
                "value_map": {"known": "mapped"},
                "fallback_value": "Other",
            },
        )

        self.assertEqual(result, "Other")

    def test_multi_value_preserve_fallback_keeps_unmapped_tokens(self):
        result = self.apply_value_map(
            "known; legacy value",
            {
                "type": "value_map",
                "question_id": "field",
                "multi_value": True,
                "value_map": {"known": "mapped"},
                "fallback_value": "preserve",
            },
        )

        self.assertEqual(result, "mapped; legacy value")


if __name__ == "__main__":
    unittest.main()
