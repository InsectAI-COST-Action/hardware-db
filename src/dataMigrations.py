# src/dataMigrations.py

"""
Data migration utilities for transforming form responses between schema versions.

This module provides functionality to apply migration mappings to historical response
data, transforming them from an old schema version to a target schema version.
"""

import json
import logging
import re
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
        elif transform_type == "fill_if_empty":
            self._apply_fill_if_empty(data, question_id, transform)
        elif transform_type == "numeric_to_range_option":
            self._apply_numeric_to_range_option(data, question_id, transform)
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
        """Map old values to new values for a question.

        When ``multi_value=True`` the field is treated as a semicolon-separated
        checkbox string.  Each token is looked up in ``value_map``; tokens with a
        ``null`` mapping are explicitly dropped, tokens absent from ``value_map``
        are preserved when ``fallback_value='preserve'`` or dropped otherwise.
        Duplicate mapped values are removed to keep the output clean.
        """
        if question_id not in data:
            return

        old_value = data[question_id]
        value_map = transform.get("value_map", {})
        fallback = transform.get("fallback_value")
        multi_value = transform.get("multi_value", False)
        separator = transform.get("separator", "; ")

        if multi_value:
            if not isinstance(old_value, str) or not old_value:
                return
            tokens = [t.strip() for t in old_value.replace(",", ";").split(";") if t.strip()]
            mapped: List[str] = []
            seen: set = set()
            for token in tokens:
                if token in value_map:
                    new_val = value_map[token]
                    if new_val is not None and new_val not in seen:
                        mapped.append(new_val)
                        seen.add(new_val)
                    # null in value_map → explicitly drop this token
                elif fallback == "preserve":
                    if token not in seen:
                        mapped.append(token)
                        seen.add(token)
                # else: no mapping entry, fallback is not "preserve" → drop
            data[question_id] = separator.join(mapped) if mapped else None
        else:
            # Simple single-value mapping
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
        """Split one question into multiple new questions.

        ``split_type='numeric_range'``: parses the source text for numeric
        values and places the first in ``target_questions[0]`` (minimum) and
        the last in ``target_questions[-1]`` (maximum).  Handles formats like
        ``"5-50"``, ``"-10 to 40"``, ``"5 - 50 mm"``, etc.

        Default behaviour (no ``split_type``) logs a warning and leaves target
        fields as ``None``.
        """
        target_questions = transform.get("target_questions", [])
        split_type = transform.get("split_type", "default")
        old_value = data.pop(source_question_id, None)

        if split_type == "numeric_range":
            text = str(old_value or "")
            # Match explicit "min-max" or "min to max" patterns.
            # Using a named separator avoids misreading "5-50" as min=5, max=-50.
            range_match = re.search(
                r'(-?\d+(?:\.\d+)?)\s*(?:to|-)\s*(-?\d+(?:\.\d+)?)',
                text, re.IGNORECASE
            )
            if range_match and len(target_questions) >= 2:
                if target_questions[0] not in data or data[target_questions[0]] is None:
                    data[target_questions[0]] = range_match.group(1)
                if target_questions[-1] not in data or data[target_questions[-1]] is None:
                    data[target_questions[-1]] = range_match.group(2)
            elif text:
                # Fallback: single number → populate first target only
                single = re.search(r'-?\d+(?:\.\d+)?', text)
                if single and target_questions:
                    if target_questions[0] not in data or data[target_questions[0]] is None:
                        data[target_questions[0]] = single.group(0)
            # Ensure all targets exist (even if None)
            for t in target_questions:
                if t not in data:
                    data[t] = None
        else:
            logger.info(
                f"Split: question '{source_question_id}' (value: '{old_value}') "
                f"→ {target_questions}. Manual mapping required if not implemented."
            )
            for new_q_id in target_questions:
                if new_q_id not in data:
                    data[new_q_id] = None
    
    def _apply_merge(
        self,
        data: Dict[str, Any],
        target_question_id: str,
        transform: Dict[str, Any]
    ) -> None:
        """Merge multiple old questions into one new question.

        When ``multi_value=True`` and a ``value_map`` is provided each source
        field is treated as a semicolon-separated checkbox string; tokens are
        mapped individually, deduplicated, then joined.  Tokens with a ``null``
        mapping are explicitly dropped; tokens absent from ``value_map`` are
        preserved when ``fallback_value='preserve'`` or dropped otherwise.

        Default behaviour concatenates non-empty source values with ``"; "``.
        """
        source_questions = transform.get("source_questions", [])
        multi_value = transform.get("multi_value", False)
        value_map = transform.get("value_map", {})
        fallback = transform.get("fallback_value")
        separator = transform.get("separator", "; ")
        dedup = transform.get("dedup", True)

        if multi_value:
            all_tokens: List[str] = []
            seen: set = set()
            for old_q_id in source_questions:
                val = data.pop(old_q_id, None)
                if not val or not isinstance(val, str):
                    continue
                tokens = [t.strip() for t in val.replace(",", ";").split(";") if t.strip()]
                for token in tokens:
                    if token in value_map:
                        new_val = value_map[token]
                        if new_val is not None:
                            if not dedup or new_val not in seen:
                                all_tokens.append(new_val)
                                seen.add(new_val)
                        # null in value_map → explicitly drop this token
                    elif fallback == "preserve":
                        if not dedup or token not in seen:
                            all_tokens.append(token)
                            seen.add(token)
                    # else: no mapping entry, fallback not "preserve" → drop
            merged_value = separator.join(all_tokens) if all_tokens else None
            data[target_question_id] = merged_value
            logger.info(
                f"Merge (multi-value): {source_questions} → '{target_question_id}' = '{merged_value}'"
            )
        else:
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

    def _apply_fill_if_empty(
        self,
        data: Dict[str, Any],
        target_question_id: str,
        transform: Dict[str, Any]
    ) -> None:
        """Copy a source field's value to the target only if the target is empty.

        The source field is always removed from the record regardless of whether
        its value was used.  This is intended for best-effort fallback mappings
        where a semantically similar (but not identical) field should fill in
        when the canonical target has no data.
        """
        source_id = transform.get("source_question_id")
        if not source_id or source_id not in data:
            return

        source_val = data.pop(source_id)
        if source_val and not data.get(target_question_id):
            data[target_question_id] = source_val
            logger.info(
                f"fill_if_empty: '{source_id}' → '{target_question_id}' = '{source_val}'"
            )
        else:
            logger.info(
                f"fill_if_empty: '{target_question_id}' already set or source empty; "
                f"dropped '{source_id}'"
            )

    def _apply_numeric_to_range_option(
        self,
        data: Dict[str, Any],
        question_id: str,
        transform: Dict[str, Any]
    ) -> None:
        """Parse a free-text numeric value and map it to a labelled range option.

        The minimum *positive* numeric value found in the string (after optional
        unit conversion to a common reference unit) is compared against a list
        of ``option_ranges`` to select the appropriate label.  Falls back to
        ``fallback_option`` if no usable number is found or no range matches.

        Example ``option_ranges`` entry::

            {"label": "2-5 cm", "min": 2, "max": 5}

        Omit ``min`` (or ``max``) to represent an open-ended bound.
        """
        if question_id not in data or not data[question_id]:
            return

        old_value = str(data[question_id])
        unit_conversion: Dict[str, float] = transform.get("unit_conversion", {})
        option_ranges: List[Dict[str, Any]] = transform.get("option_ranges", [])
        fallback = transform.get("fallback_option", "Other (please specify)")

        # Find all (number, optional_unit) pairs
        matches = re.findall(r'(-?\d+(?:\.\d+)?)\s*(mm|cm|m)?', old_value.lower())

        values_converted: List[float] = []
        for num_str, unit in matches:
            num = float(num_str)
            if num <= 0:
                continue  # ignore zero/negative (e.g. separator hyphens)
            if unit and unit in unit_conversion:
                num *= unit_conversion[unit]
            values_converted.append(num)

        if not values_converted:
            data[question_id] = fallback
            return

        min_val = min(values_converted)
        result = fallback
        for opt in option_ranges:
            low = opt.get("min", float("-inf"))
            high = opt.get("max", float("inf"))
            if low <= min_val < high:
                result = opt["label"]
                break

        data[question_id] = result
        logger.info(
            f"numeric_to_range_option: '{question_id}' parsed min={min_val} → '{result}'"
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
    
    For sequential migrations (e.g., 0.2.0 → 1.0.0 → 1.1.0-beta), this applies
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
    
    # Try direct migration first
    migration = registry.get_migration(source_version, target_version)
    if migration is not None:
        return migration.apply_to_response(response)
    
    # Try to find a chain of migrations
    chain = _find_migration_chain(source_version, target_version, registry)
    if chain is None:
        raise MigrationError(
            f"No migration path from {source_version} to {target_version}"
        )
    
    # Apply migrations sequentially
    current = response
    for step_source, step_target in chain:
        step_migration = registry.get_migration(step_source, step_target)
        if step_migration is None:
            raise MigrationError(
                f"Migration step {step_source}→{step_target} not found in chain"
            )
        current = step_migration.apply_to_response(current)
    
    return current


def _find_migration_chain(
    source_version: str,
    target_version: str,
    registry: MigrationRegistry
) -> Optional[List[Tuple[str, str]]]:
    """
    Find a chain of migrations from source to target using BFS.
    
    Returns:
        List of (source, target) tuples representing the migration path,
        or None if no path exists.
    """
    available = registry.list_available_migrations()
    
    # Build adjacency map
    graph: Dict[str, List[str]] = {}
    for src, tgt in available:
        if src not in graph:
            graph[src] = []
        graph[src].append(tgt)
    
    if source_version not in graph:
        return None
    
    # BFS to find shortest path
    from collections import deque
    queue: deque = deque([(source_version, [])])
    visited = {source_version}
    
    while queue:
        current, path = queue.popleft()
        for neighbor in graph.get(current, []):
            new_path = path + [(current, neighbor)]
            if neighbor == target_version:
                return new_path
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    
    return None


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
