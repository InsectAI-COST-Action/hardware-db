# Schema Versioning and Migrations

## Quick Commands

```bash
python tests/validateSchema.py --verbose
python reprocessData.py --dry-run --verbose
python reprocessData.py --verbose
python -m json.tool schemas/migrations/migrations.json
```

## Migration Registry Shape

Each migration in schemas/migrations/migrations.json uses:

```json
{
  "mappings": {
    "drops": ["old_question_id"],
    "adds": [
      {
        "question_id": "new_question_id",
        "title": "New Question",
        "type": "text",
        "default_value": null
      }
    ],
    "renames": [
      { "old_id": "old_name", "new_id": "new_name" }
    ],
    "transforms": []
  }
}
```

Execution order in src/dataMigrations.py:

1. Keep all non-dropped keys
2. Apply renames
3. Apply transforms
4. Add missing new fields with defaults
5. Update _metadata migration fields

## Supported Transform Types

### value_map

Maps values for one question.

Options:
- value_map: dictionary of old to new values
- fallback_value: preserve, null, or fixed value
- multi_value: true for semicolon/comma separated checkbox strings
- separator: output separator (default ; )

### split

Splits one source into multiple targets.

Options:
- split_type: numeric_range
- target_questions: [min_field, max_field]

numeric_range parses forms like 5-50 and -10 to 40.

### merge

Merges multiple source questions into one target.

Options:
- source_questions: list of old fields
- multi_value: true for token-wise merge/mapping
- value_map: optional per-token normalization map
- fallback_value: preserve or drop unmatched tokens
- dedup: true to deduplicate merged tokens
- separator: output separator

### fill_if_empty

Best-effort fallback mapping.

Options:
- question_id: target field
- source_question_id: source field copied only when target is empty

### numeric_to_range_option

Parses numeric free text and maps to labeled ranges.

Options:
- question_id: target field
- option_ranges: list of labels with min/max bounds
- unit_conversion: optional unit normalization factors
- fallback_option: value when parsing fails

### custom

Recognized but intentionally skipped (warning only).

## Current Important Migration

1.0.0 to 1.1.0-beta currently includes:

- drop list cleanup for removed legacy fields
- additional renames for documentation, institution, costs, and size fields
- value normalization for file_types, capture_modes, and power_sources
- multi-source connectivity merge
- numeric range splits for subject size and temperature
- focal distance mapping to range options
- maintainer to contributor fallback copy when contributor fields are empty

## Rules to Keep Stable

- Never change existing question IDs in place
- Prefer renames over drop and add when semantics are equivalent
- Use transforms when value formats or option labels changed
- Run dry-run before writing real data

## File Reference

- Main schema: hardware-db_schema.json
- Historical schemas: schemas/hardware-db_schema_v*.json
- Migration registry: schemas/migrations/migrations.json
- Migration schema: schemas/migrations/migration_schema.json
- Migration engine: src/dataMigrations.py
- Reprocessing CLI: reprocessData.py
