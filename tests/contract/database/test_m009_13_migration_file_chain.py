from pathlib import Path

from database.migration_control.manifest import MigrationManifestLoader


ROOT = Path(__file__).parents[3]
MIGRATIONS = ROOT / "database/migrations"


def test_manifest_expected_objects_are_declared_by_corresponding_forward_sql():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    for definition in catalogue.definitions:
        sql = (MIGRATIONS / definition.forward.relative_path).read_text(encoding="utf-8")
        for table in definition.expected_objects.tables:
            assert table in sql
        for index in definition.expected_objects.indexes:
            assert index in sql
        for schema in definition.expected_objects.schemas:
            assert f"SCHEMA IF NOT EXISTS {schema}" in sql


def test_every_rollback_companion_drops_only_objects_owned_by_or_after_its_layer():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    for definition in catalogue.definitions:
        rollback = (MIGRATIONS / definition.rollback.relative_path).read_text(encoding="utf-8")
        for table in definition.expected_objects.tables:
            assert table.split(".", 1)[-1] in rollback
