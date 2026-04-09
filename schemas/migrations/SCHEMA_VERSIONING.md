# Schema Versioning & Data Migrations Guide

## Quick Start

### Commands at a Glance

```bash
# Validate current schema
python tests/validateSchema.py --verbose

# Reprocess all data from current version to target version
python reprocessData.py --verbose

# Reprocess with dry-run (preview changes without writing)
python reprocessData.py --dry-run --verbose

# View migration registry structure
cat schemas/migrations/migrations.json
```

### Common Workflow: Adding a New Schema Version

1. **Create new schema version** (e.g., `1.1.0`):
   - Modify `hardware-db_schema.json`
   - Update `_metadata.schema_version` to new version
   - Ensure all question IDs remain immutable

2. **Define the migration** in `schemas/migrations/migrations.json`:
```json
{
  "1.0.0→1.1.0": {
    "created_date": "2026-04-09",
    "description": "Added new sensor fields",
    "mappings": {
      "drops": [],
      "adds": [
        {"id": "sensor_type", "title": "Sensor Type", "type": "multiple_choice"}
      ],
      "renames": [],
      "transforms": []
    }
  }
}
```

3. **Archive old schema**:
```bash
cp hardware-db_schema.json schemas/hardware-db_schema_v1.0.0.json
```

4. **Validate and test**:
```bash
python tests/validateSchema.py --verbose
python reprocessData.py --dry-run --verbose
```

5. **Apply migrations** to real data:
```bash
python reprocessData.py --verbose
```

---

## Concepts

### Semantic Versioning

Schema versions follow **MAJOR.MINOR.PATCH** format:
- **MAJOR**: Breaking changes (backward-incompatible)
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

Example: `1.2.3` = Major version 1, 2 minor features, 3 patches

### Question IDs (Immutable Keys)

Each question has a unique **`id`** field that **never changes**. This is the primary key for data mapping:

```json
{
  "id": "device_name",
  "title": "Device Name",
  "type": "short_text"
}
```

Even if you rename the question title, the `id` remains the same, and historical data stays linked correctly.

### Metadata Tracking

Each collected response includes `_metadata`:
```json
{
  "_metadata": {
    "schema_version": "1.0.0",
    "collected_from_form_id": "abc123",
    "collected_date": "2026-04-08T15:30:00Z",
    "migrated_from_version": null
  },
  "device_name": "Server A",
  "...": "..."
}
```

The `migrated_from_version` field indicates if this response was migrated up from an older schema version.

### Data Archive Strategy

- **Current form**: `hardware-db_schema.json` (used by collectResponses.py)
- **Historical versions**: `schemas/hardware-db_schema_v{VERSION}.json` (read-only reference)
- **All collected data**: `data/form_responses.csv` (can contain responses from multiple schema versions)

---

## Workflow: Handling Schema Changes

### Scenario 1: Adding a New Question (MINOR version bump)

1. Add the new question to `hardware-db_schema.json`
2. Generate new version file: `schemas/hardware-db_schema_v1.0.0.json` (old version)
3. Update `_metadata.schema_version` to `1.1.0` in main schema
4. Define migration in `migrations.json`:
```json
"1.0.0→1.1.0": {
  "created_date": "2026-04-09",
  "description": "Added sensor_type field",
  "mappings": {
    "drops": [],
    "adds": [
      {
        "id": "sensor_type",
        "title": "Sensor Type",
        "type": "multiple_choice",
        "default_value": "Unknown"
      }
    ],
    "renames": [],
    "transforms": []
  }
}
```

5. Run `reprocessData.py` to add `null` or default values to old responses

### Scenario 2: Renaming a Question (PATC or MINOR version bump depends on scope)

```json
"1.1.0→1.1.1": {
  "created_date": "2026-04-10",
  "description": "Renamed 'device_name' to 'equipment_name'",
  "mappings": {
    "drops": [],
    "adds": [],
    "renames": [
      {"old_id": "device_name", "new_id": "equipment_name"}
    ],
    "transforms": []
  }
}
```

### Scenario 3: Consolidating Two Questions (MAJOR version bump)

```json
"1.1.1→2.0.0": {
  "created_date": "2026-04-11",
  "description": "Merged model and serial into equipment_id; removed model_number",
  "mappings": {
    "drops": ["model_number"],
    "adds": [],
    "renames": [],
    "transforms": [
      {
        "id": "equipment_id",
        "type": "merge",
        "source_ids": ["model_number", "serial_number"],
        "separator": "-"
      }
    ]
  }
}
```

### Scenario 4: Value Mapping (e.g., Standardizing Choices)

```json
"1.0.0→1.0.1": {
  "description": "Standardized condition values",
  "mappings": {
    "drops": [],
    "adds": [],
    "renames": [],
    "transforms": [
      {
        "id": "condition_status",
        "type": "value_map",
        "mapping": {
          "good": "Functional",
          "broken": "Non-Functional",
          "working": "Functional",
          "repair": "Needs Repair"
        }
      }
    ]
  }
}
```

---

## Transformation Types

### 1. **value_map**
Replaces values according to a mapping dictionary.

```json
{
  "id": "condition",
  "type": "value_map",
  "mapping": {
    "G": "Good",
    "D": "Damaged",
    "L": "Lost"
  }
}
```

### 2. **split**
Splits a single field into multiple fields using a regex pattern.

```json
{
  "id": "model_serial",
  "type": "split",
  "split_regex": "^([A-Z0-9]+)-(.+)$",
  "new_fields": ["model", "serial"]
}
```

### 3. **merge**
Combines multiple fields into one, optionally with a separator.

```json
{
  "id": "full_identifier",
  "type": "merge",
  "source_ids": ["brand", "model", "serial"],
  "separator": " | "
}
```

### 4. **format**
Applies a format transformation (e.g., uppercase, lowercase, date formatting).

```json
{
  "id": "device_name",
  "type": "format",
  "format": "uppercase"
}
```

---

## Best Practices

### ✅ DO:
- **Use semantic versioning** consistently
- **Never change question IDs** — create new ones instead
- **Document migrations** with clear descriptions
- **Test migrations** with `--dry-run` before applying
- **Archive old versions** in `schemas/` directory
- **Commit migrations** to version control with schema changes
- **Validate schemas** regularly: `python tests/validateSchema.py --verbose`

### ❌ DON'T:
- Don't manually edit `form_responses.csv` — use reprocessData.py
- Don't skip validation before applying migrations
- Don't delete old schema versions unless certain they won't be needed
- Don't use generic IDs like `q1`, `q2` — use descriptive names like `device_type`, `serial_number`

---

## Troubleshooting

### Migration Not Applying?

1. **Check migration registry path:**
   ```bash
   ls -la schemas/migrations/
   ```
   Ensure `migrations.json` exists and is valid JSON.

2. **Validate the migration definition:**
   ```bash
   python -m json.tool schemas/migrations/migrations.json
   ```

3. **Check schema version format:**
   ```bash
   python tests/validateSchema.py --verbose
   ```

### Question IDs Not Found During Migration?

1. **Verify question exists** in `hardware-db_schema.json`
2. **Check ID spelling** — IDs are case-sensitive
3. **Review migration mappings** — ensure all referenced IDs exist

### Data Loss Concerns?

1. **Always backup** before running: `python reprocessData.py` creates automatic backups
2. **Use `--dry-run`** first: `python reprocessData.py --dry-run --verbose`
3. **Review CSV backup**: Check `data/form_responses_backup_[timestamp].csv`

---

## File Reference

- **Main Schema**: `hardware-db_schema.json`
- **Migration Registry**: `schemas/migrations/migrations.json`
- **Migration Validator**: `schemas/migrations/migration_schema.json`
- **Migration Engine**: `src/data_migrations.py`
- **Migration CLI**: `reprocessData.py`
- **Schema Validator**: `tests/validateSchema.py`
- **Test Data**: `data/form_responses.csv`
