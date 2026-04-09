"""
Schema validation utilities for hardware-db schema files.

Validates JSON schema structure, versioning format, and business rules
like unique question IDs.
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import jsonschema

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def load_validation_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON Schema validation file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema_structure(
    schema_file: Path,
    validation_schema_file: Path
) -> Tuple[bool, List[str]]:
    """
    Validate schema structure against JSON Schema validation rules.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, [f"Cannot load schema file: {e}"]
    
    try:
        validation_schema = load_validation_schema(validation_schema_file)
    except (json.JSONDecodeError, IOError) as e:
        return False, [f"Cannot load validation schema file: {e}"]
    
    try:
        jsonschema.validate(instance=schema, schema=validation_schema)
    except jsonschema.ValidationError as e:
        errors.append(f"JSON Schema validation failed: {e.message}")
        errors.append(f"  Path: {'.'.join(str(p) for p in e.path)}")
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid validation schema: {e.message}")
    
    return len(errors) == 0, errors


def check_unique_question_ids(schema_file: Path) -> Tuple[bool, List[str]]:
    """
    Check that all question IDs are unique within the schema.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, [f"Cannot load schema file: {e}"]
    
    seen_ids: Dict[str, str] = {}  # id -> section where first seen
    
    sections = schema.get("sections", [])
    for section in sections:
        section_id = section.get("id", "unknown")
        questions = section.get("questions", [])
        
        for question in questions:
            q_id = question.get("id")
            
            if not q_id:
                errors.append(f"Question in section '{section_id}' has no 'id' field")
                continue
            
            if q_id in seen_ids:
                errors.append(
                    f"Duplicate question ID '{q_id}': "
                    f"first seen in '{seen_ids[q_id]}', also in '{section_id}'"
                )
            else:
                seen_ids[q_id] = section_id
    
    return len(errors) == 0, errors


def check_version_format(schema_file: Path) -> Tuple[bool, List[str]]:
    """
    Check that schema version is valid semantic versioning.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return False, [f"Cannot load schema file: {e}"]
    
    metadata = schema.get("_metadata", {})
    version = metadata.get("schema_version", "")
    
    if not version:
        errors.append("Missing '_metadata.schema_version'")
        return False, errors
    
    parts = version.split(".")
    if len(parts) != 3:
        errors.append(
            f"Invalid schema_version '{version}': "
            f"must be MAJOR.MINOR.PATCH format"
        )
        return False, errors
    
    for i, part in enumerate(parts):
        try:
            int(part)
        except ValueError:
            part_name = ["MAJOR", "MINOR", "PATCH"][i]
            errors.append(
                f"Invalid schema_version '{version}': "
                f"{part_name} component '{part}' is not an integer"
            )
    
    return len(errors) == 0, errors


def validate_all(
    schema_file: Path,
    validation_schema_file: Path,
    verbose: bool = False
) -> bool:
    """
    Run all validation checks on the schema file.
    
    Returns:
        True if all checks pass, False otherwise
    """
    checks = [
        ("Version format", lambda: check_version_format(schema_file)),
        ("Unique question IDs", lambda: check_unique_question_ids(schema_file)),
        ("JSON Schema structure", lambda: validate_schema_structure(schema_file, validation_schema_file)),
    ]
    
    all_passed = True
    
    print(f"Validating schema: {schema_file}\n")
    
    for check_name, check_func in checks:
        is_valid, errors = check_func()
        
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"{status}: {check_name}")
        
        if not is_valid:
            all_passed = False
            for error in errors:
                print(f"  - {error}")
        elif verbose:
            print("  All checks passed")
        
        print()
    
    return all_passed


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate hardware database schema")
    parser.add_argument(
        "schema_file",
        type=Path,
        nargs="?",
        default=Path("hardware-db_schema.json"),
        help="Path to schema file (default: hardware-db_schema.json)"
    )
    parser.add_argument(
        "--validation-schema",
        type=Path,
        default=Path("tests/validation_schema.json"),
        help="Path to validation schema (default: tests/validation_schema.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        is_valid = validate_all(
            args.schema_file,
            args.validation_schema,
            verbose=args.verbose
        )
        
        if is_valid:
            print("✓ All validation checks passed!")
            sys.exit(0)
        else:
            print("✗ Validation failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
