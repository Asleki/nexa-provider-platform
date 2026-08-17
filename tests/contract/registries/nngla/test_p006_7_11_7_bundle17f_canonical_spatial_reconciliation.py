from collections import Counter
from registries.nngla.spatial_fabric.bundle17f import (
    bundle17f_is_qualified,
    derive_existing_canonical_alignment,
    derive_geometry_traversal_qualifications,
    derive_spatial_association_precondition_results,
    remaining_noncanonical_road_candidate_ids,
)
from registries.nngla.spatial_fabric.bundle17f.contracts import CanonicalSubjectFamily


def test_bundle17f_contract_reconciles_locked_700_192_350_21_21_snapshot_without_regeneration():
    rows = derive_existing_canonical_alignment()
    assert Counter(x.object_family.value for x in rows) == Counter({
        "PLACE": 700,
        "ADMINISTRATIVE_AREA": 192,
        "ROAD": 350,
        "GEOGRAPHIC_FEATURE": 21,
        "EXISTING_GEOMETRY": 21,
    })
    assert len({x.canonical_id for x in rows if x.object_family is CanonicalSubjectFamily.ROAD}) == 350
    assert len(remaining_noncanonical_road_candidate_ids()) == 550


def test_bundle17f_contract_extends_existing_identities_only_when_real_geometry_evidence_exists():
    pre = derive_spatial_association_precondition_results()
    assert Counter(x.precondition_status for x in pre) == Counter({
        "DEFERRED_NO_GEOMETRY": 1242,
        "PASS_READY_TO_ASSOCIATE": 20,
        "DEFERRED_SUBJECT_ROLE_RECONCILIATION": 1,
    })
    assert all(x.traversal_status == "PASS" for x in derive_geometry_traversal_qualifications())


def test_bundle17f_contract_closes_before_cadastre_without_requiring_new_sql_or_fake_spatial_rows():
    assert bundle17f_is_qualified()
