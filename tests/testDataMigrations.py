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

    def test_multi_value_keeps_commas_inside_tokens(self):
        value = "Hymenoptera (bees, wasps, ants); Diptera (flies, mosquitoes)"
        result = self.apply_value_map(
            value,
            {
                "type": "value_map",
                "question_id": "field",
                "multi_value": True,
                "value_map": {
                    "Hymenoptera (bees, wasps, ants)": "Hymenoptera (bees, wasps, ants)",
                    "Diptera (flies, mosquitoes)": "Diptera (flies, mosquitoes)",
                },
                "fallback_value": "preserve",
            },
        )

        self.assertEqual(result, value)

    def test_multi_value_can_opt_in_to_comma_input_separator(self):
        result = self.apply_value_map(
            "legacy one, legacy two",
            {
                "type": "value_map",
                "question_id": "field",
                "multi_value": True,
                "input_separator": ",",
                "value_map": {
                    "legacy one": "mapped one",
                    "legacy two": "mapped two",
                },
            },
        )

        self.assertEqual(result, "mapped one; mapped two")

    def test_multi_value_merge_keeps_commas_inside_tokens(self):
        migration = SchemaMigration(
            "1.0.0",
            "1.1.0",
            {
                "drops": [],
                "adds": [],
                "renames": [],
                "transforms": [
                    {
                        "type": "merge",
                        "question_id": "field",
                        "source_questions": ["first", "second"],
                        "multi_value": True,
                        "value_map": {
                            "Hymenoptera (bees, wasps, ants)": "Hymenoptera (bees, wasps, ants)",
                            "Diptera (flies, mosquitoes)": "Diptera (flies, mosquitoes)",
                        },
                        "fallback_value": "preserve",
                    }
                ],
            },
        )

        result = migration.apply_to_response(
            {
                "first": "Hymenoptera (bees, wasps, ants)",
                "second": "Diptera (flies, mosquitoes)",
            }
        )["field"]

        self.assertEqual(
            result,
            "Hymenoptera (bees, wasps, ants); Diptera (flies, mosquitoes)",
        )

    def test_multi_value_merge_can_opt_in_to_comma_input_separator(self):
        migration = SchemaMigration(
            "1.0.0",
            "1.1.0",
            {
                "drops": [],
                "adds": [],
                "renames": [],
                "transforms": [
                    {
                        "type": "merge",
                        "question_id": "field",
                        "source_questions": ["first"],
                        "multi_value": True,
                        "input_separator": ",",
                        "value_map": {
                            "legacy one": "mapped one",
                            "legacy two": "mapped two",
                        },
                    }
                ],
            },
        )

        result = migration.apply_to_response({"first": "legacy one, legacy two"})[
            "field"
        ]

        self.assertEqual(result, "mapped one; mapped two")


if __name__ == "__main__":
    unittest.main()
