import json
from pathlib import Path

from registries.nngla.spatial_fabric.bundle17e import (
    MemorySpatialRepository,
    artifact_drift_findings,
    build_spatial_preview,
    bundle17e_is_qualified,
    derive_effective_dated_assignments,
    derive_geometry_assignments,
    derive_persistence_qualifications,
    derive_spatial_canonical_crosswalk,
)

ROOT = Path(__file__).resolve().parents[4]


def test_bundle17e_closes_spatial_persistence_contract_without_new_sql_migration_or_old_row_rewrite():
    assert bundle17e_is_qualified() is True
    assert len(derive_spatial_canonical_crosswalk()) == 2411
    assert len(derive_geometry_assignments()) == 2411
    assert len(derive_effective_dated_assignments()) == 2411
    assert len(derive_persistence_qualifications()) == 2411
    assert artifact_drift_findings() == ()

    manifest = json.loads((ROOT / "database" / "migrations" / "migration_manifest.json").read_text())
    migration_ids = [item["migration_id"] for item in manifest["migrations"]]
    assert len(migration_ids) == 10
    assert not any("17e" in item.lower() or "spatial_fabric" in item.lower() for item in migration_ids)


def test_bundle17e_preview_exposes_all_mandatory_fail_closed_fields_and_zero_writes():
    preview = build_spatial_preview(MemorySpatialRepository().snapshot())
    assert preview.execution_ready is True
    assert preview.database_writes == 0
    assert len(preview.fingerprint) == 64
    sample = preview.items[0]
    for name in (
        "selected", "source_verified", "coordinate_valid", "map_reconciled", "crs_valid", "precision_valid",
        "containment_valid", "topology_valid", "environment_resolved", "conflict_free", "qualified", "quarantined",
        "database_writes", "fingerprint",
    ):
        assert hasattr(sample, name)
    assert all(item.qualified and not item.quarantined and item.database_writes == 0 for item in preview.items)
