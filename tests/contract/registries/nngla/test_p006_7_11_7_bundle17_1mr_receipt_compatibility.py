"""Contract locks for P006.7.11.7 Bundle 17.1MR."""
import hashlib
from pathlib import Path
import json

from registries.nngla.migration_ready import orchestrator
from registries.nngla.migration_ready.catalogue import ROOT


LOCKED_17E_PERSISTENCE_SHA256 = "c5a70830070fb794f72d2f4691d09c87ca6fbb63"


def test_17_1mr_preserves_plan_lineage_without_schema_migration_19():
    manifest = json.loads((ROOT / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["migrations"]) == 18
    assert max(row["sequence_number"] for row in manifest["migrations"]) == 18
    assert all("migration_ready" not in row["migration_id"] for row in manifest["migrations"])
    assert orchestrator.PLAN_ID == "P006.7.11.7.0MR-SPATIAL-BATCH"
    assert orchestrator.PLAN_VERSION == 2


def test_locked_execution_foundation_unique_fingerprint_target_contract_remains_intact():
    sql = (ROOT / "database/migrations/m006_07_11_nngla_execution_foundation.sql").read_text(encoding="utf-8")
    normalized = " ".join(sql.split())
    assert (
        "CREATE UNIQUE INDEX ux_nngla_execution_fingerprint_target ON "
        "geography.nngla_execution_receipt(fingerprint_sha256,database_name,environment_name);"
    ) in normalized


def test_17_1mr_derives_transaction_receipt_identity_instead_of_reusing_authorization_identity():
    source = (ROOT / "registries/nngla/migration_ready/orchestrator.py").read_text(encoding="utf-8")
    assert "def _batch_receipt_fingerprint(" in source
    assert "fingerprint=batch_receipt_fingerprint" in source
    assert "authorization_fingerprint={preview.fingerprint}" in source
    assert "fingerprint=preview.fingerprint" not in source


def test_locked_bundle17e_persistence_file_is_not_modified_by_17_1mr():
    path = ROOT / "registries/nngla/spatial_fabric/bundle17e/persistence.py"
    # Git blob SHA from the supplied committed predecessor repository.
    header = f"blob {path.stat().st_size}\0".encode("utf-8")
    git_blob_sha = hashlib.sha1(header + path.read_bytes()).hexdigest()
    assert git_blob_sha == LOCKED_17E_PERSISTENCE_SHA256
