"""Immutable contracts for repository-side migration discovery and planning."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from collections.abc import Mapping

from .constants import DIRECTIONS, SHA256_HEX_LENGTH, TRANSACTION_POLICIES
from .errors import MigrationIdentityError, MigrationManifestError


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MigrationManifestError(f"{field_name} is required.")
    return value.strip()


def _validate_sha256(value: str, field_name: str) -> str:
    text = _required_text(value, field_name).lower()
    if len(text) != SHA256_HEX_LENGTH or any(ch not in "0123456789abcdef" for ch in text):
        raise MigrationManifestError(f"{field_name} must be a 64-character SHA-256 hex digest.")
    return text


@dataclass(frozen=True, slots=True, order=True)
class MigrationIdentity:
    sequence_number: int
    migration_id: str
    milestone_id: str
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.sequence_number, int) or self.sequence_number < 1:
            raise MigrationIdentityError("migration sequence_number must be a positive integer.")
        for field_name in ("migration_id", "milestone_id", "description"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise MigrationIdentityError(f"{field_name} is required.")


@dataclass(frozen=True, slots=True)
class ExpectedObjects:
    schemas: tuple[str, ...] = ()
    tables: tuple[str, ...] = ()
    indexes: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    views: tuple[str, ...] = ()
    functions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("schemas", "tables", "indexes", "constraints", "views", "functions"):
            values = tuple(getattr(self, field_name))
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise MigrationManifestError(f"expected_objects.{field_name} contains an invalid value.")
            if len(values) != len(set(values)):
                raise MigrationManifestError(f"expected_objects.{field_name} contains duplicates.")
            object.__setattr__(self, field_name, values)


@dataclass(frozen=True, slots=True)
class MigrationArtifact:
    relative_path: str
    direction: str
    sha256: str
    byte_size: int
    transaction_policy: str

    def __post_init__(self) -> None:
        path = PurePosixPath(_required_text(self.relative_path, "relative_path"))
        if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
            raise MigrationManifestError("migration artifact path must be a safe root-relative filename.")
        if self.direction not in DIRECTIONS:
            raise MigrationManifestError(f"unsupported migration direction: {self.direction}")
        object.__setattr__(self, "sha256", _validate_sha256(self.sha256, "sha256"))
        if not isinstance(self.byte_size, int) or self.byte_size < 1:
            raise MigrationManifestError("migration artifact byte_size must be positive.")
        if self.transaction_policy not in TRANSACTION_POLICIES:
            raise MigrationManifestError(f"unsupported transaction policy: {self.transaction_policy}")


@dataclass(frozen=True, slots=True)
class MigrationDefinition:
    identity: MigrationIdentity
    forward: MigrationArtifact
    rollback: MigrationArtifact
    depends_on: tuple[str, ...]
    expected_objects: ExpectedObjects
    destructive: bool = False
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        dependencies = tuple(self.depends_on)
        if len(dependencies) != len(set(dependencies)):
            raise MigrationManifestError(f"duplicate dependencies for {self.identity.migration_id}.")
        if self.identity.migration_id in dependencies:
            raise MigrationManifestError("a migration cannot depend on itself.")
        if self.forward.direction != "forward" or self.rollback.direction != "rollback":
            raise MigrationManifestError("migration artifacts are assigned to the wrong directions.")
        object.__setattr__(self, "depends_on", dependencies)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata or {})))


@dataclass(frozen=True, slots=True)
class MigrationCatalogue:
    definitions: tuple[MigrationDefinition, ...]
    manifest_digest: str
    manifest_schema: str
    manifest_schema_version: int

    def __post_init__(self) -> None:
        definitions = tuple(self.definitions)
        ids = tuple(item.identity.migration_id for item in definitions)
        if len(ids) != len(set(ids)):
            raise MigrationManifestError("migration catalogue contains duplicate migration IDs.")
        object.__setattr__(self, "definitions", definitions)
        object.__setattr__(self, "manifest_digest", _validate_sha256(self.manifest_digest, "manifest_digest"))

    def by_id(self) -> Mapping[str, MigrationDefinition]:
        return MappingProxyType({item.identity.migration_id: item for item in self.definitions})


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    forward_order: tuple[MigrationDefinition, ...]
    rollback_order: tuple[MigrationDefinition, ...]
    plan_checksum: str
    manifest_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "forward_order", tuple(self.forward_order))
        object.__setattr__(self, "rollback_order", tuple(self.rollback_order))
        object.__setattr__(self, "plan_checksum", _validate_sha256(self.plan_checksum, "plan_checksum"))
        object.__setattr__(self, "manifest_digest", _validate_sha256(self.manifest_digest, "manifest_digest"))

    @property
    def migration_count(self) -> int:
        return len(self.forward_order)


__all__ = [
    "MigrationIdentity",
    "ExpectedObjects",
    "MigrationArtifact",
    "MigrationDefinition",
    "MigrationCatalogue",
    "MigrationPlan",
]
