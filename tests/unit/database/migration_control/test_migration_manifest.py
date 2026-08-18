import json
from pathlib import Path

import pytest

from database.migration_control.errors import MigrationDuplicateError, MigrationManifestError
from database.migration_control.manifest import MigrationManifestLoader


ROOT = Path(__file__).parents[4]
MANIFEST = ROOT / "database/migrations/migration_manifest.json"


def test_real_manifest_loads_five_immutable_definitions():
    catalogue = MigrationManifestLoader().load(MANIFEST)
    assert len(catalogue.definitions) == 18
    assert catalogue.manifest_schema == "npp.database-migration-manifest"
    assert len(catalogue.manifest_digest) == 64
    assert catalogue.definitions[0].identity.milestone_id == "M009.10.4"


def test_duplicate_sequence_is_rejected(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["migrations"][1]["sequence_number"] = data["migrations"][0]["sequence_number"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(MigrationDuplicateError):
        MigrationManifestLoader().load(path)


def test_manifest_missing_dependency_field_is_rejected(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    del data["migrations"][0]["depends_on"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(MigrationManifestError):
        MigrationManifestLoader().load(path)


def test_filename_milestone_disagreement_is_rejected(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["migrations"][0]["milestone_id"] = "M009.10.5"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(Exception):
        MigrationManifestLoader().load(path)
