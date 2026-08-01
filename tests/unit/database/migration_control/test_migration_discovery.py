import shutil
from pathlib import Path

import pytest

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.errors import MigrationDiscoveryError, MigrationPathError
from database.migration_control.manifest import MigrationManifestLoader


ROOT = Path(__file__).parents[4]
SOURCE = ROOT / "database/migrations"


def copy_migrations(target: Path) -> Path:
    shutil.copytree(SOURCE, target, symlinks=True)
    return target


def test_real_migration_directory_contains_only_approved_artifacts():
    catalogue = MigrationManifestLoader().load(SOURCE / "migration_manifest.json")
    assert MigrationDiscovery(SOURCE).validate_catalogue(catalogue) is catalogue


def test_unknown_sql_file_blocks_discovery(tmp_path):
    root = copy_migrations(tmp_path / "migrations")
    (root / "unapproved.sql").write_text("SELECT 1;", encoding="utf-8")
    catalogue = MigrationManifestLoader().load(root / "migration_manifest.json")
    with pytest.raises(MigrationDiscoveryError):
        MigrationDiscovery(root).validate_catalogue(catalogue)


def test_symlinked_approved_artifact_is_rejected(tmp_path):
    root = copy_migrations(tmp_path / "migrations")
    approved = root / "m009_10_04_name_catalogue.sql"
    outside = tmp_path / "outside.sql"
    outside.write_bytes(approved.read_bytes())
    approved.unlink()
    approved.symlink_to(outside)
    catalogue = MigrationManifestLoader().load(root / "migration_manifest.json")
    with pytest.raises(MigrationPathError):
        MigrationDiscovery(root).validate_catalogue(catalogue)


def test_byte_size_change_is_detected_before_execution(tmp_path):
    root = copy_migrations(tmp_path / "migrations")
    artifact = root / "m009_10_04_name_catalogue.sql"
    artifact.write_bytes(artifact.read_bytes() + b"\n")
    catalogue = MigrationManifestLoader().load(root / "migration_manifest.json")
    with pytest.raises(MigrationDiscoveryError):
        MigrationDiscovery(root).validate_catalogue(catalogue)
