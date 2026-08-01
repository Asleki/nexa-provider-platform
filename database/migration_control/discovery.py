"""Safe discovery and exact approval checks for migration artifacts."""
from __future__ import annotations

from pathlib import Path

from .constants import ALLOWED_STATIC_FILENAMES
from .contracts import MigrationCatalogue
from .errors import MigrationDiscoveryError, MigrationPairingError, MigrationPathError
from .checksums import verify_checksum


class MigrationDiscovery:
    def __init__(self, migration_root: str | Path):
        self.migration_root = Path(migration_root).resolve()
        if not self.migration_root.is_dir():
            raise MigrationDiscoveryError("migration root does not exist or is not a directory.")

    def validate_catalogue(self, catalogue: MigrationCatalogue) -> MigrationCatalogue:
        approved = set(ALLOWED_STATIC_FILENAMES)
        for definition in catalogue.definitions:
            approved.add(definition.forward.relative_path)
            approved.add(definition.rollback.relative_path)
            self._validate_artifact(definition.forward.relative_path, definition.forward.byte_size, definition.forward.sha256)
            self._validate_artifact(definition.rollback.relative_path, definition.rollback.byte_size, definition.rollback.sha256)
        actual = {path.name for path in self.migration_root.iterdir()}
        unknown = sorted(actual - approved)
        missing = sorted(approved - actual - {".gitkeep"})
        if unknown:
            raise MigrationDiscoveryError(f"unapproved files exist in migration root: {', '.join(unknown)}")
        if missing:
            raise MigrationPairingError(f"approved migration files are missing: {', '.join(missing)}")
        return catalogue

    def _validate_artifact(self, relative_path: str, expected_size: int, expected_sha256: str) -> Path:
        candidate = self.migration_root / relative_path
        if candidate.is_symlink():
            raise MigrationPathError(f"symlinked migration artifacts are prohibited: {relative_path}")
        resolved = candidate.resolve()
        if resolved.parent != self.migration_root:
            raise MigrationPathError(f"migration path escapes approved root: {relative_path}")
        if not resolved.is_file():
            raise MigrationPairingError(f"migration artifact is missing: {relative_path}")
        actual_size = resolved.stat().st_size
        if actual_size != expected_size:
            raise MigrationDiscoveryError(
                f"byte-size mismatch for {relative_path}: expected {expected_size}, got {actual_size}."
            )
        verify_checksum(resolved, expected_sha256)
        return resolved


__all__ = ["MigrationDiscovery"]
