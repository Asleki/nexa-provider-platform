import csv

from registries.nngla.spatial_fabric.bundle17e import artifact_drift_findings, artifact_rows, write_bundle17e_artifacts


def test_bundle17e_artifact_contract_has_exactly_ten_required_csvs_and_governed_empty_execution_registers(tmp_path):
    paths = write_bundle17e_artifacts(tmp_path)
    assert len(paths) == 10
    rows = artifact_rows()
    assert len(rows["canonical_crosswalk"]) == 2411
    assert len(rows["geometry_assignments"]) == 2411
    assert len(rows["effective_assignments"]) == 2411
    assert len(rows["persistence_qualification"]) == 2411
    assert len(rows["spatial_qualification"]) == 2411
    assert len(rows["batch_manifest"]) == 1
    assert rows["quarantine"] == ()
    assert rows["execution_receipts"] == ()
    assert rows["execution_items"] == ()
    for path in paths:
        assert path.is_file() and path.stat().st_size > 0
        with path.open(encoding="utf-8-sig", newline="") as handle:
            assert next(csv.reader(handle))
    assert artifact_drift_findings(tmp_path) == ()


def test_authoritative_execution_evidence_is_not_fabricated_before_live_postgresql_execution():
    rows = artifact_rows()
    manifest = rows["batch_manifest"][0]
    assert manifest["database_writes"] == "0"
    assert manifest["execution_ready"] == "false"
    assert manifest["execution_state"] == "NOT_EXECUTED_LIVE_TARGET_CONFIRMATION_REQUIRED"
    assert rows["execution_receipts"] == ()
    assert rows["execution_items"] == ()
