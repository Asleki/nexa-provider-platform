import pytest

from registries.nngla.spatial_realization.authority_adoption.contracts import (
    CandidateSourceMode, CityAuthorityAdoptionRequest, CityQualificationReceipt,
    CityQualificationStatus, PrecisionMode, PrecisionPolicy, SOURCE_EXACT_PRECISION,
    stable_digest,
)

SHA = "a" * 64


def _receipt(**overrides):
    data = dict(
        qualification_id="city-qualification:nngla:" + "1" * 64,
        city_administrative_area_id="NG-ADM-000009", root_place_id="NG-PLC-000001",
        candidate_source_mode=CandidateSourceMode.FROZEN_SOURCE_REUSE,
        candidate_id="NG-ADM-BND-000009", raw_candidate_geometry_sha256=SHA,
        evaluated_candidate_geometry_sha256=SHA, source_geometry_sha256="b"*64,
        source_dataset_id="dataset:nngla:admin", source_dataset_version="v1",
        source_path_reference="data/admin.geojson", fabric_run_id="", package_sha256="",
        validation_parent_id="NG-ADM-000001", parent_evidence_kind="LOCKED_FROZEN_REFERENCE",
        parent_evidence_id="NG-ADM-BND-000001", raw_parent_geometry_sha256="c"*64,
        evaluated_parent_geometry_sha256="c"*64, parent_qualification_reference="BUNDLE19B",
        parent_source_path_reference="data/admin.geojson", peer_evidence_digest="d"*64,
        precision_policy_id=SOURCE_EXACT_PRECISION.policy_id,
        precision_policy_sha256=SOURCE_EXACT_PRECISION.policy_sha256,
        precision_mode=PrecisionMode.SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP,
        precision_grid_size_degrees=None, precision_evidence_reference=SOURCE_EXACT_PRECISION.evidence_reference,
        valid_geometry=True, polygonal=True, non_empty=True, srid_correct=True,
        parent_evidence_valid=True, city_covered_by_parent=True,
        raw_area_outside_parent_m2=0.0, area_outside_parent_m2=0.0,
        raw_positive_city_peer_overlap_m2=0.0, positive_city_peer_overlap_m2=0.0,
        raw_positive_municipality_overlap_m2=0.5, positive_municipality_overlap_m2=0.5,
        reference_point_covered=True, unresolved_city_affecting_defect_count=0,
        numerical_residue=False, source_provenance_bound=True, qualifier_actor_id="actor:qualifier",
        runtime_mode="production", status=CityQualificationStatus.CITY_READY_FOR_AUTHORITY,
        failed_predicates=(), database_mutation=False,
    )
    data.update(overrides)
    return CityQualificationReceipt(**data)


def test_source_exact_policy_is_hash_bound_and_has_no_grid():
    assert SOURCE_EXACT_PRECISION.grid_size_degrees is None
    assert len(SOURCE_EXACT_PRECISION.policy_sha256) == 64


def test_governed_precision_requires_explicit_grid_and_evidence():
    p = PrecisionPolicy(policy_id="precision-policy:nngla:test", mode=PrecisionMode.GOVERNED_COMMON_PRECISION,
                        grid_size_degrees=1e-9, evidence_reference="decision:precision:test")
    assert p.grid_size_degrees == 1e-9
    with pytest.raises(ValueError):
        PrecisionPolicy(policy_id="x", mode=PrecisionMode.GOVERNED_COMMON_PRECISION, evidence_reference="e")


def test_city_receipt_separates_municipality_overlap_from_feature_qualified_status():
    receipt = _receipt()
    assert receipt.feature_qualified
    assert receipt.positive_municipality_overlap_m2 == 0.5


def test_city_receipt_is_always_read_only():
    with pytest.raises(ValueError):
        _receipt(database_mutation=True)


def test_qualification_digest_is_deterministic():
    a = _receipt(); b = _receipt()
    assert a.qualification_sha256 == b.qualification_sha256
    assert len(a.qualification_sha256) == 64


def test_reconstructed_candidate_requires_delivery2_binding():
    with pytest.raises(ValueError):
        # validated through CityCandidateEvidence contract in package import path
        from registries.nngla.spatial_realization.authority_adoption.contracts import CityCandidateEvidence
        CityCandidateEvidence("NG-ADM-000009","NG-PLC-000001",CandidateSourceMode.SHARED_FACE_RECONSTRUCTION,
            "fabric-candidate:nngla:x",SHA,SHA,"d","v","p","production","00")


def test_adoption_requires_three_distinct_actors():
    receipt = _receipt()
    with pytest.raises(ValueError):
        CityAuthorityAdoptionRequest(
            qualification_id=receipt.qualification_id, qualification_sha256=receipt.qualification_sha256,
            city_administrative_area_id=receipt.city_administrative_area_id, candidate_id=receipt.candidate_id,
            candidate_geometry_sha256=receipt.evaluated_candidate_geometry_sha256,
            candidate_source_mode=receipt.candidate_source_mode, validation_parent_id=receipt.validation_parent_id,
            parent_evidence_id=receipt.parent_evidence_id, parent_geometry_sha256=receipt.evaluated_parent_geometry_sha256,
            parent_qualification_reference=receipt.parent_qualification_reference, peer_evidence_digest=receipt.peer_evidence_digest,
            precision_policy_id=receipt.precision_policy_id, precision_policy_sha256=receipt.precision_policy_sha256,
            effective_on="2026-08-28", qualifier_actor_id="actor:q", submitter_actor_id="actor:q",
            approver_actor_id="actor:a", decision_reference="decision:1", rationale="approved exact CITY authority",
        )
