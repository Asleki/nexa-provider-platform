from collections import Counter
from registries.nngla.spatial_fabric.bundle17f import (
    derive_spatial_association_precondition_results,
    derive_subject_spatial_association_candidates,
)
from registries.nngla.spatial_fabric.bundle17f.contracts import AssociationStatus


def test_association_candidates_preserve_missing_geometry_as_deferred_not_fabricated():
    rows = derive_subject_spatial_association_candidates()
    assert len(rows) == 1263
    counts = Counter(x.association_status for x in rows)
    assert counts[AssociationStatus.DEFERRED_NO_GEOMETRY] == 1242
    deferred = [x for x in rows if x.association_status is AssociationStatus.DEFERRED_NO_GEOMETRY]
    assert all(x.geometry_id == "" for x in deferred)


def test_twenty_feature_subjects_can_reuse_existing_geometry_without_new_identity():
    rows = derive_subject_spatial_association_candidates()
    ready = [x for x in rows if x.association_status is AssociationStatus.READY_ASSOCIATE_EXISTING_GEOMETRY]
    assert len(ready) == 20
    assert ready[0].canonical_subject_id == "NG-FEAT-000002"
    assert ready[0].geometry_id == "NG-GEO-000002"
    assert ready[-1].canonical_subject_id == "NG-FEAT-000021"
    assert ready[-1].geometry_id == "NG-GEO-000021"


def test_mainland_feature_is_not_silently_equated_with_country_boundary_geometry():
    row = next(x for x in derive_subject_spatial_association_candidates() if x.canonical_subject_id == "NG-FEAT-000001")
    assert row.association_status is AssociationStatus.SUBJECT_ROLE_RECONCILIATION_REQUIRED
    assert row.geometry_id == ""
    assert row.source_geometry_subject_id == "country:novegeo"


def test_preconditions_pass_only_for_real_existing_geometry_and_defer_others():
    rows = derive_spatial_association_precondition_results()
    assert len(rows) == 1263
    counts = Counter(x.precondition_status for x in rows)
    assert counts["PASS_READY_TO_ASSOCIATE"] == 20
    assert counts["DEFERRED_NO_GEOMETRY"] == 1242
    assert counts["DEFERRED_SUBJECT_ROLE_RECONCILIATION"] == 1
    assert counts["FAIL"] == 0
