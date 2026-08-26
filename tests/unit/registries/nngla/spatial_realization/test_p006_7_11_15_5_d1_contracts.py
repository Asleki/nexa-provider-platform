from dataclasses import replace

import pytest

from registries.nngla.spatial_realization.contracts import (
    FaceAssignmentDecision,
    FaceDecisionKind,
    FabricInput,
    FabricInputRole,
    FabricLevel,
    FabricRuntimeSignature,
    ParentFabricScope,
)


def signature():
    return FabricRuntimeSignature(
        engine_family="SHAPELY_READ_ONLY_PROTOTYPE",
        python_version="3.12",
        geometry_engine_version="2.1.2",
        geos_version="3.13.1",
        projection_engine_version="3.7.2",
        proj_version="9.5.0",
        topology_crs="EPSG:4326",
        diagnostic_crs="EPSG:6933",
        precision_policy_id="SOURCE_COORDINATES_NO_SNAP",
    )


def input_row(role, subject_id, kind="CITY"):
    return FabricInput(
        input_role=role,
        subject_id=subject_id,
        administrative_type_code=kind,
        canonical_name=subject_id,
        source_candidate_id="admbnd:test:" + subject_id,
        geometry_checksum_sha256="0" * 64,
        source_path_reference="bundle19b.geojson",
    )


def test_delivery1_runtime_signature_and_scope_fingerprint_are_stable():
    sig = signature()
    assert len(sig.digest) == 64
    scope = ParentFabricScope(
        scope_id="fabric-scope:nngla:test",
        requested_root_place_id="NG-PLC-000086",
        parent=input_row(FabricInputRole.PARENT, "NG-ADM-000032"),
        level=FabricLevel.CITY_DISTRICTS,
        exhaustive_siblings=(
            input_row(FabricInputRole.EXHAUSTIVE_SIBLING, "NG-ADM-000036", "CITY_DISTRICT"),
            input_row(FabricInputRole.EXHAUSTIVE_SIBLING, "NG-ADM-000037", "CITY_DISTRICT"),
        ),
        overlays=(input_row(FabricInputRole.NON_EXHAUSTIVE_OVERLAY, "NG-ADM-000053", "INDUSTRIAL_ZONE"),),
        runtime_signature=sig,
        input_digest="1" * 64,
    )
    assert len(scope.fingerprint) == 64
    assert scope.fingerprint == replace(scope).fingerprint


def test_delivery1_scope_rejects_overlay_as_exhaustive_owner():
    with pytest.raises(ValueError, match="overlay"):
        ParentFabricScope(
            scope_id="fabric-scope:nngla:test",
            requested_root_place_id="NG-PLC-000086",
            parent=input_row(FabricInputRole.PARENT, "NG-ADM-000032"),
            level=FabricLevel.CITY_DISTRICTS,
            exhaustive_siblings=(input_row(FabricInputRole.EXHAUSTIVE_SIBLING, "NG-ADM-000053", "INDUSTRIAL_ZONE"),),
            overlays=(input_row(FabricInputRole.NON_EXHAUSTIVE_OVERLAY, "NG-ADM-000053", "INDUSTRIAL_ZONE"),),
            runtime_signature=signature(),
            input_digest="1" * 64,
        )


def test_delivery1_face_assignment_requires_hash_owner_and_evidence():
    decision = FaceAssignmentDecision(
        face_id="fabric-face:nngla:" + "a" * 64,
        face_geometry_sha256="b" * 64,
        owner_subject_id="NG-ADM-000037",
        decision_kind=FaceDecisionKind.TEST_ONLY_GOVERNANCE_FIXTURE,
        decision_reference="TEST-ONLY:fixture-001",
        rationale="Non-authoritative fixture proving deterministic convergence only.",
    )
    assert decision.owner_subject_id == "NG-ADM-000037"
    with pytest.raises(ValueError):
        replace(decision, owner_subject_id="district-x")
