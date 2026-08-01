"""Migration filename parsing and stable identity validation."""
from __future__ import annotations

from dataclasses import dataclass

from .constants import MIGRATION_FILENAME_PATTERN
from .errors import MigrationIdentityError


@dataclass(frozen=True, slots=True)
class ParsedMigrationFilename:
    filename: str
    migration_id: str
    milestone_id: str
    description: str
    direction: str
    parent_segment: int
    minor_segment: int
    leaf_segment: int


def parse_migration_filename(filename: str) -> ParsedMigrationFilename:
    if not isinstance(filename, str):
        raise MigrationIdentityError("migration filename must be text.")
    rollback = filename.endswith("_rollback.sql")
    parse_target = filename[:-13] + ".sql" if rollback else filename
    match = MIGRATION_FILENAME_PATTERN.fullmatch(parse_target)
    if match is None:
        raise MigrationIdentityError(f"invalid migration filename: {filename}")
    parent_text = match.group("parent")
    minor_text = match.group("minor")
    leaf_text = match.group("leaf")
    description = match.group("description")
    stem = f"m{parent_text}_{minor_text}_{leaf_text}_{description}"
    milestone_id = f"M{int(parent_text):03d}.{int(minor_text)}.{int(leaf_text)}"
    return ParsedMigrationFilename(
        filename=filename,
        migration_id=stem,
        milestone_id=milestone_id,
        description=description,
        direction="rollback" if rollback else "forward",
        parent_segment=int(parent_text),
        minor_segment=int(minor_text),
        leaf_segment=int(leaf_text),
    )


def validate_filename_identity(
    filename: str,
    *,
    expected_migration_id: str,
    expected_milestone_id: str,
    expected_direction: str,
) -> ParsedMigrationFilename:
    parsed = parse_migration_filename(filename)
    if parsed.migration_id != expected_migration_id:
        raise MigrationIdentityError(
            f"filename migration ID {parsed.migration_id} does not match {expected_migration_id}."
        )
    if parsed.milestone_id != expected_milestone_id:
        raise MigrationIdentityError(
            f"filename milestone {parsed.milestone_id} does not match {expected_milestone_id}."
        )
    if parsed.direction != expected_direction:
        raise MigrationIdentityError(
            f"filename direction {parsed.direction} does not match {expected_direction}."
        )
    return parsed


__all__ = ["ParsedMigrationFilename", "parse_migration_filename", "validate_filename_identity"]
