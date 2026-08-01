"""Loading and semantic validation for the committed migration manifest."""
from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping

from .checksums import sha256_bytes
from .constants import MANIFEST_SCHEMA, MANIFEST_SCHEMA_VERSION
from .contracts import (
    ExpectedObjects,
    MigrationArtifact,
    MigrationCatalogue,
    MigrationDefinition,
    MigrationIdentity,
)
from .errors import MigrationDuplicateError, MigrationManifestError
from .naming import validate_filename_identity


_REQUIRED_ROOT_FIELDS = {"manifest_schema", "manifest_schema_version", "catalogue_version", "migrations"}
_REQUIRED_MIGRATION_FIELDS = {
    "migration_id",
    "milestone_id",
    "sequence_number",
    "description",
    "forward_file",
    "rollback_file",
    "forward_sha256",
    "rollback_sha256",
    "forward_byte_size",
    "rollback_byte_size",
    "depends_on",
    "transaction_policy",
    "expected_objects",
    "destructive",
}


class MigrationManifestLoader:
    def load(self, manifest_path: str | Path) -> MigrationCatalogue:
        path = Path(manifest_path)
        raw_bytes = path.read_bytes()
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MigrationManifestError(f"cannot read migration manifest: {exc}") from exc
        if not isinstance(data, dict):
            raise MigrationManifestError("migration manifest root must be an object.")
        missing = _REQUIRED_ROOT_FIELDS - set(data)
        if missing:
            raise MigrationManifestError(f"migration manifest is missing fields: {', '.join(sorted(missing))}")
        if data["manifest_schema"] != MANIFEST_SCHEMA:
            raise MigrationManifestError("unsupported migration manifest schema.")
        if data["manifest_schema_version"] != MANIFEST_SCHEMA_VERSION:
            raise MigrationManifestError("unsupported migration manifest schema version.")
        rows = data["migrations"]
        if not isinstance(rows, list) or not rows:
            raise MigrationManifestError("migration manifest requires at least one migration.")
        definitions = tuple(self._definition(row) for row in rows)
        ids = [item.identity.migration_id for item in definitions]
        sequences = [item.identity.sequence_number for item in definitions]
        if len(ids) != len(set(ids)):
            raise MigrationDuplicateError("migration manifest contains duplicate migration IDs.")
        if len(sequences) != len(set(sequences)):
            raise MigrationDuplicateError("migration manifest contains duplicate sequence numbers.")
        return MigrationCatalogue(
            definitions=definitions,
            manifest_digest=sha256_bytes(raw_bytes),
            manifest_schema=data["manifest_schema"],
            manifest_schema_version=data["manifest_schema_version"],
        )

    def _definition(self, row: object) -> MigrationDefinition:
        if not isinstance(row, Mapping):
            raise MigrationManifestError("each migration manifest row must be an object.")
        missing = _REQUIRED_MIGRATION_FIELDS - set(row)
        if missing:
            raise MigrationManifestError(f"migration row is missing fields: {', '.join(sorted(missing))}")
        identity = MigrationIdentity(
            sequence_number=int(row["sequence_number"]),
            migration_id=str(row["migration_id"]),
            milestone_id=str(row["milestone_id"]),
            description=str(row["description"]),
        )
        forward_file = str(row["forward_file"])
        rollback_file = str(row["rollback_file"])
        validate_filename_identity(
            forward_file,
            expected_migration_id=identity.migration_id,
            expected_milestone_id=identity.milestone_id,
            expected_direction="forward",
        )
        validate_filename_identity(
            rollback_file,
            expected_migration_id=identity.migration_id,
            expected_milestone_id=identity.milestone_id,
            expected_direction="rollback",
        )
        transaction_policy = str(row["transaction_policy"])
        expected = row["expected_objects"]
        if not isinstance(expected, Mapping):
            raise MigrationManifestError("expected_objects must be an object.")
        return MigrationDefinition(
            identity=identity,
            forward=MigrationArtifact(
                relative_path=forward_file,
                direction="forward",
                sha256=str(row["forward_sha256"]),
                byte_size=int(row["forward_byte_size"]),
                transaction_policy=transaction_policy,
            ),
            rollback=MigrationArtifact(
                relative_path=rollback_file,
                direction="rollback",
                sha256=str(row["rollback_sha256"]),
                byte_size=int(row["rollback_byte_size"]),
                transaction_policy=transaction_policy,
            ),
            depends_on=tuple(str(value) for value in row["depends_on"]),
            expected_objects=ExpectedObjects(
                schemas=tuple(expected.get("schemas", ())),
                tables=tuple(expected.get("tables", ())),
                indexes=tuple(expected.get("indexes", ())),
                constraints=tuple(expected.get("constraints", ())),
                views=tuple(expected.get("views", ())),
                functions=tuple(expected.get("functions", ())),
            ),
            destructive=bool(row["destructive"]),
            metadata={"catalogue_entry_version": int(row.get("catalogue_entry_version", 1))},
        )


__all__ = ["MigrationManifestLoader"]
