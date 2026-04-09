# src/dataMigrations.py

"""
Data migration utilities for transforming form responses between schema versions.

This module provides functionality to apply migration mappings to historical response
data, transforming them from an old schema version to a target schema version.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Raised when migration operations fail."""
    pass


class SchemaMigration:
    """
    Encapsulates a migration from one schema version to another.
    
    Attributes:
        source_version: The starting schema version (e.g., "1.0.0")
        target_version: The target schema version (e.g., "1.1.0")
        mappings: Dictionary containing drops, adds, renames, and transforms
    """
    
    def __init__(
        self, 
        source_version: str, 
        target_version: str, 
        mappings: Dict[str, Any]
    ):
        self.source_version = source_version
        self.target_version = target_version
        self.mappings = mappings
        self._validate_mappings()
    
    def _validate_mappings(self) -> None:
        """Validate that mappings contain required keys."""
        required_keys = {"drops", "adds", "renames", "transforms"}
        if not all(key in self.mappings for key in required_keys):
            raise MigrationError(
                f"Mappings must contain keys: {required_keys}. "
                f"Got: {set(self.mappings.keys())}"
            )
    
    def apply_to_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply this migration to a single response object.
        
        Args:
            response: Response dictionary with question IDs as keys
            
        Returns:
            Migrated response dictionary with keys matching target schema
        """
        migrated = {}
        
        # Step 1: Start with identity (all old keys that aren't dropped)
        drops = set(self.mappings.get("drops", []))
        for key, value in response.items():
            if key not in drops and key != "_metadata":
                migrated[key] = value
        
        # Step 2: Apply renames
        renames = {r["old_id"]: r["new_id"] for r in self.mappings.get("renames", [])}
        for old_id, new_id in renames.items():
            if old_id in migrated:
                migrated[new_id] = migrated.pop(old_id)
        
        # Step 3: Apply transforms (value mappings, splits, merges)
        for transform in self.mappings.get("transforms", []):
            self._apply_transform(migrated, transform)
        
        # Step 4: Add new questions with defaults
        for add in self.mappings.get("adds", []):
            question_id = add["question_id"]
            if question_id not in migrated:
                migrated[question_id] = add.get("default_value")
        
        # Step 5: Preserve and update metadata
        if "_metadata" in response:
            migrated["_metadata"] = response["_metadata"].copy()
        else:
            migrated["_metadata"] = {}
        
        # Record the migration in metadata
        if "migrated_from_version" not in migrated["_metadata"]:
            migrated["_metadata"]["migrated_from_version"] = self.source_version
        migrated["_metadata"]["migrated_to_version"] = self.target_version
        migrated["_metadata"]["last_migration_date"] = datetime.utcnow().isoformat() + "Z"
        
        return migrated
    
    def _apply_transform(self, data: Dict[str, Any], transform: Dict[str, Any]) -> None:
        """
        Apply a single transformation to the data dictionary.
        
        Args:
            data: Response data dictionary (modified in-place)
            transform: Transformation specification
        """
        question_id = transform["question_id"]
        transform_type = transform["type"]
        
        if transform_type == "value_map":
            self._apply_value_map(data, question_id, transform)
        elif transform_type == "split":
            self._apply_split(data, question_id, transform)
        elif transform_type == "merge":
            self._apply_merge(data, question_id, transform)
        elif transform_type == "custom":
            logger.warning(
                f"Custom transform for '{question_id}' not implemented; skipping"
            )
        else:
            raise MigrationError(f"Unknown transform type: {transform_type}")
    
    def _apply_value_map(
        self, 
        data: Dict[str, Any], 
        question_id: str, 
        transform: Dict[str, Any]
    ) -> None:
        """Map old values to new values for a question."""
        if question_id not in data:
            return
        
        old_value = data[question_id]
        value_map = transform.get("value_map", {})
        fallback = transform.get("fallback_value")
        
        # Map the value; use fallback if not found
        if old_value in value_map:
            data[question_id] = value_map[old_value]
        elif fallback is not None:
            data[question_id] = fallback
        else:
            logger.warning(
                f"Value '{old_value}' for question '{question_id}' not in mapping; "
                f"preserving original"
            )
    
    def _apply_split(
        self, 
        data: Dict[str, Any], 
        source_question_id: str, 
        transform: Dict[str, Any]
    ) -> None:
        """
        Split one question into multiple new questions.
        
        For now, this is a placeholder that removes the old question and adds
        empty placeholders for new questions. Custom logic would be needed
        to parse/split the actual value.
        """
        target_questions = transform.get("target_questions", [])
        old_value = data.pop(source_question_id, None)
        
        logger.info(
            f"Split: question '{source_question_id}' (value: '{old_value}') "
            f"→ {target_questions}. Manual mapping required if not implemented."
        )
        
        # Add placeholder values for new questions
        for new_q_id in target_questions:
            if new_q_id not in data:
                data[new_q_id] = None
    
    def _apply_merge(
        self, 
        data: Dict[str, Any], 
        target_question_id: str, 
        transform: Dict[str, Any]
    ) -> None:
        """
        Merge multiple old questions into one new question.
        
        For now, this concatenates values with a separator. Custom logic would
        be needed for more sophisticated merging.
        """
        source_questions = transform.get("source_questions", [])
        values = []
        
        for old_q_id in source_questions:
            if old_q_id in data and data[old_q_id]:
                values.append(str(data[old_q_id]))
            data.pop(old_q_id, None)
        
        merged_value = "; ".join(values) if values else None
        data[target_question_id] = merged_value
        
        logger.info(
            f"Merge: {source_questions} → '{target_question_id}' = '{merged_value}'"
        )


class MigrationRegistry:
    """
    Manages a registry of schema migrations loaded from a JSON file.
    """
    
    def __init__(self, registry_path: Path):
        """
        Load migration registry from JSON file.
        
        Args:
            registry_path: Path to migrations/migrations.json
        """
        self.registry_path = Path(registry_path)
        self.migrations: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load and parse the migrations registry."""
        if not self.registry_path.exists():
            logger.warning(f"Migration registry not found: {self.registry_path}")
            return
        
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.migrations = data.get("migrations", {})
            logger.info(
                f"Loaded {len(self.migrations)} migration(s) from {self.registry_path}"
            )
        except (json.JSONDecodeError, IOError) as e:
            raise MigrationError(f"Failed to load migration registry: {e}")
    
    def get_migration(
        self, 
        source_version: str, 
        target_version: str
    ) -> Optional[SchemaMigration]:
        """
        Retrieve a migration between two versions.
        
        Args:
            source_version: Source schema version
            target_version: Target schema version
            
        Returns:
            SchemaMigration object, or None if not found
        """
        key = f"{source_version}→{target_version}"
        if key not in self.migrations:
            logger.warning(
                f"No migration defined from {source_version} to {target_version}"
            )
            return None
        
        mappings = self.migrations[key].get("mappings", {})
        return SchemaMigration(source_version, target_version, mappings)
    
    def list_available_migrations(self) -> List[Tuple[str, str]]:
        """
        List all available migration paths.
        
        Returns:
            List of (source_version, target_version) tuples
        """
        paths = []
        for key in self.migrations.keys():
            if "→" in key:
                source, target = key.split("→")
                paths.append((source, target))
        return paths


def migrate_response(
    response: Dict[str, Any],
    source_version: str,
    target_version: str,
    registry: MigrationRegistry
) -> Dict[str, Any]:
    """
    Migrate a single response from source to target schema version.
    
    For sequential migrations (e.g., 1.0.0 → 1.1.0 → 1.2.0), this applies
    each migration in sequence. If only a direct migration exists, it uses that.
    
    Args:
        response: Response dictionary
        source_version: Current schema version
        target_version: Desired schema version
        registry: MigrationRegistry instance
        
    Returns:
        Migrated response dictionary
    """
    if source_version == target_version:
        return response
    
    # For now, support only direct migrations
    # (Future: implement version chain resolution)
    migration = registry.get_migration(source_version, target_version)
    if migration is None:
        raise MigrationError(
            f"No migration path from {source_version} to {target_version}"
        )
    
    return migration.apply_to_response(response)


def migrate_responses_batch(
    responses: List[Dict[str, Any]],
    source_version: str,
    target_version: str,
    registry: MigrationRegistry,
    on_error: str = "warn"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Migrate a batch of responses from source to target schema version.
    
    Args:
        responses: List of response dictionaries
        source_version: Current schema version
        target_version: Desired schema version
        registry: MigrationRegistry instance
        on_error: Error handling ("warn" = log and skip, "raise" = propagate)
        
    Returns:
        (successful_responses, failed_responses) tuples
    """
    successful = []
    failed = []
    
    for idx, response in enumerate(responses):
        try:
            migrated = migrate_response(
                response, source_version, target_version, registry
            )
            successful.append(migrated)
        except Exception as e:
            error_info = {
                "index": idx,
                "response": response,
                "error": str(e)
            }
            if on_error == "raise":
                raise MigrationError(
                    f"Migration failed at index {idx}: {e}"
                ) from e
            else:
                logger.warning(f"Failed to migrate response {idx}: {e}")
                failed.append(error_info)
    
    logger.info(
        f"Batch migration: {len(successful)} successful, {len(failed)} failed"
    )
    return successful, failed
