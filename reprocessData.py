"""
Reprocess historical form responses through schema migrations.

This script walks through all JSON files in the data/ directory, checks their
schema version against the current schema, and applies any necessary migrations
to bring them to the current version.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.dataMigrations import MigrationRegistry, migrate_response, MigrationError
from src.misc_helpers import sanitize_filename, slugify
from configParsing import build_config


# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("reprocessing.log")
    ]
)
logger = logging.getLogger(__name__)


# Configuration keys needed
SCHEMA_FILE = ""
CURRENT_SCHEMA_VERSION = ""
DATA_DIR = "data"
MIGRATIONS_REGISTRY = "schemas/migrations/migrations.json"
BACKUP_SUFFIX = ".backup"
DEBUG = False


def load_schema_version(schema_path: str) -> str:
    """Extract schema version from schema JSON file."""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema.get("_metadata", {}).get("schema_version", "1.0.0")
    except Exception as e:
        logger.error(f"Failed to load schema version from {schema_path}: {e}")
        raise


def load_response_json(json_path: Path) -> Dict[str, Any]:
    """Load a response JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        raise
    except IOError as e:
        logger.error(f"Cannot read {json_path}: {e}")
        raise


def save_response_json(
    json_path: Path, 
    data: Dict[str, Any], 
    backup: bool = True
) -> None:
    """Save a response JSON file, optionally creating a backup."""
    if backup and json_path.exists():
        backup_path = json_path.with_suffix(json_path.suffix + BACKUP_SUFFIX)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup for {json_path}: {e}")
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated: {json_path}")
    except IOError as e:
        logger.error(f"Failed to write {json_path}: {e}")
        raise


def reprocess_single_file(
    json_path: Path,
    current_version: str,
    registry: MigrationRegistry,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Reprocess a single response JSON file.
    
    Returns:
        Status dict with keys: file, old_version, new_version, migrated, error
    """
    status = {
        "file": str(json_path),
        "old_version": None,
        "new_version": current_version,
        "migrated": False,
        "error": None
    }
    
    try:
        response = load_response_json(json_path)
        
        # Get response version (from metadata or default to 1.0.0)
        response_version = (
            response.get("_metadata", {}).get("schema_version", "1.0.0")
        )
        status["old_version"] = response_version
        
        if response_version == current_version:
            logger.info(f"{json_path.name}: already at version {current_version}")
            return status
        
        # Attempt migration
        logger.info(
            f"{json_path.name}: migrating from {response_version} "
            f"to {current_version}"
        )
        
        migrated_response = migrate_response(
            response, response_version, current_version, registry
        )
        
        # Ensure schema version is updated in metadata
        if "_metadata" not in migrated_response:
            migrated_response["_metadata"] = {}
        migrated_response["_metadata"]["schema_version"] = current_version
        
        if not dry_run:
            save_response_json(json_path, migrated_response, backup=True)
        
        status["migrated"] = True
        logger.info(f"{json_path.name}: ✓ migrated successfully")
        
    except MigrationError as e:
        status["error"] = f"Migration failed: {str(e)}"
        logger.error(f"{json_path.name}: {status['error']}")
    except Exception as e:
        status["error"] = f"Unexpected error: {str(e)}"
        logger.error(f"{json_path.name}: {status['error']}")
    
    return status


def reprocess_all(
    dry_run: bool = False,
    verbose: bool = False
) -> None:
    """
    Reprocess all response JSON files in data/ directory.
    
    Args:
        dry_run: If True, don't actually write changes
        verbose: If True, print extra debug info
    """
    cfg = build_config(globals())
    
    current_version = load_schema_version(cfg["SCHEMA_FILE"])
    logger.info(f"Current schema version: {current_version}")
    
    # Load migration registry
    registry_path = Path(cfg.get("MIGRATIONS_REGISTRY", "migrations/migrations.json"))
    registry = MigrationRegistry(registry_path)
    
    # Find all JSON files in data directory
    data_dir = Path(cfg.get("DATA_DIR", "data"))
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return
    
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        logger.info(f"No JSON files found in {data_dir}")
        return
    
    logger.info(f"Found {len(json_files)} JSON file(s) to process")
    
    if dry_run:
        logger.warning("DRY RUN MODE: no files will be modified")
    
    # Process each file
    results = []
    for json_path in sorted(json_files):
        # Skip if it looks like a backup or metadata file
        if json_path.name.endswith(BACKUP_SUFFIX):
            continue
        if json_path.name.startswith("form_responses"):
            logger.debug(f"Skipping non-device file: {json_path.name}")
            continue
        
        status = reprocess_single_file(
            json_path, current_version, registry, dry_run=dry_run
        )
        results.append(status)
    
    # Summary
    logger.info("\n" + "="*60 + " REPROCESSING SUMMARY " + "="*60)
    
    migrated_count = sum(1 for r in results if r["migrated"])
    unchanged_count = sum(1 for r in results if not r["migrated"] and not r["error"])
    error_count = sum(1 for r in results if r["error"])
    
    logger.info(f"Total files: {len(results)}")
    logger.info(f"  - Migrated:  {migrated_count}")
    logger.info(f"  - Unchanged: {unchanged_count}")
    logger.info(f"  - Errors:    {error_count}")
    
    if error_count > 0:
        logger.warning("\nFailed migrations:")
        for result in results:
            if result["error"]:
                logger.warning(f"  {Path(result['file']).name}: {result['error']}")
    
    if dry_run:
        logger.info("\n(DRY RUN - no files were actually modified)")
    else:
        logger.info(f"\nReprocessing complete. See reprocessing.log for details.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reprocess historical form responses through schema migrations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose debug information"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting reprocessing at {datetime.utcnow().isoformat()}Z")
    
    try:
        reprocess_all(dry_run=args.dry_run, verbose=args.verbose)
        logger.info("Reprocessing completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Reprocessing failed: {e}")
        sys.exit(1)
