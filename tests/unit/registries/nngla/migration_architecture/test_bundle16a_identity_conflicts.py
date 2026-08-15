from registries.nngla.migration_architecture import (
    CANONICAL_NAMESPACE_CONTRACTS,
    CanonicalIdentityAllocator,
    CanonicalIdentityError,
    CanonicalObjectFamily,
    ConflictCode,
    ConflictDisposition,
    ConflictEvaluator,
    ExistingCrosswalk,
    SourceIdentity,
)


def _source(source_id: str, candidate_id: str | None = None) -> SourceIdentity:
    return SourceIdentity("dataset:novegeo:test", "1", source_id, candidate_id)


def test_canonical_namespaces_are_runtime_independent_and_immutable():
    for contract in CANONICAL_NAMESPACE_CONTRACTS.values():
        assert contract.runtime_scoped is False
        assert contract.immutable_after_issue is True
        assert contract.validates(contract.example)


def test_place_admin_and_road_ids_are_proposed_from_governed_suffixes():
    allocator = CanonicalIdentityAllocator()
    place = allocator.propose(
        source=_source("NGP-000123"),
        object_family=CanonicalObjectFamily.PLACE,
    )
    admin = allocator.propose(
        source=_source("NGR-01", "NG-ADM-CAND-000042"),
        object_family=CanonicalObjectFamily.ADMINISTRATIVE_AREA,
    )
    road = allocator.propose(
        source=_source("road-source:77", "NG-RD-CAND-000077"),
        object_family=CanonicalObjectFamily.ROAD,
    )
    assert place.canonical_id == "NG-PLC-000123"
    assert admin.canonical_id == "NG-ADM-000042"
    assert road.canonical_id == "NG-RD-000077"


def test_allocator_rejects_sources_without_a_governed_six_digit_allocation_basis():
    allocator = CanonicalIdentityAllocator()
    try:
        allocator.propose(source=_source("NGR-01"), object_family=CanonicalObjectFamily.ADMINISTRATIVE_AREA)
    except CanonicalIdentityError as exc:
        assert "six-digit suffix" in str(exc)
    else:
        raise AssertionError("non-governed allocation basis was accepted")


def test_proposal_collision_detection_is_read_only_and_explicit():
    allocator = CanonicalIdentityAllocator()
    proposals = (
        allocator.propose(source=_source("NGP-000001"), object_family=CanonicalObjectFamily.PLACE),
        allocator.propose(source=_source("OTHER-000001"), object_family=CanonicalObjectFamily.PLACE),
    )
    conflicts = allocator.detect_proposal_collisions(proposals)
    assert len(conflicts) == 1
    assert conflicts[0].canonical_id == "NG-PLC-000001"
    assert conflicts[0].source_record_ids == ("NGP-000001", "OTHER-000001")


def test_existing_crosswalk_exact_replay_is_idempotent_reuse():
    evaluator = ConflictEvaluator()
    payload = {"source_place_code": "NGP-000001", "canonical_name": "Orivane"}
    existing = ExistingCrosswalk(
        "NGP-000001",
        "NG-PLC-000001",
        1,
        evaluator.payload_sha256(payload),
    )
    decision = evaluator.evaluate_existing_crosswalk(
        source_record_id="NGP-000001",
        proposed_canonical_id="NG-PLC-000001",
        proposed_payload=payload,
        existing=existing,
    )
    assert decision.reusable is True
    assert decision.findings[0].code is ConflictCode.IDEMPOTENT_REUSE
    assert decision.findings[0].disposition is ConflictDisposition.REUSE


def test_same_source_identity_with_changed_payload_is_quarantined():
    evaluator = ConflictEvaluator()
    original = {"canonical_name": "Orivane"}
    existing = ExistingCrosswalk(
        "NGP-000001",
        "NG-PLC-000001",
        1,
        evaluator.payload_sha256(original),
    )
    decision = evaluator.evaluate_existing_crosswalk(
        source_record_id="NGP-000001",
        proposed_canonical_id="NG-PLC-000001",
        proposed_payload={"canonical_name": "Different"},
        existing=existing,
    )
    assert decision.requires_quarantine is True
    assert decision.findings[0].code is ConflictCode.SOURCE_ID_CONFLICT


def test_existing_crosswalk_to_another_canonical_id_blocks_execution():
    evaluator = ConflictEvaluator()
    payload = {"canonical_name": "Orivane"}
    existing = ExistingCrosswalk(
        "NGP-000001",
        "NG-PLC-000099",
        1,
        evaluator.payload_sha256(payload),
    )
    decision = evaluator.evaluate_existing_crosswalk(
        source_record_id="NGP-000001",
        proposed_canonical_id="NG-PLC-000001",
        proposed_payload=payload,
        existing=existing,
    )
    assert decision.blocks_execution is True
    assert decision.findings[0].code is ConflictCode.CROSSWALK_CONFLICT


def test_coordinate_contract_uses_longitude_then_latitude_ranges():
    evaluator = ConflictEvaluator()
    assert evaluator.validate_coordinate(subject_id="point:ok", longitude=30.5, latitude=-17.8).findings == ()
    bad = evaluator.validate_coordinate(subject_id="point:bad", longitude=181, latitude=-17.8)
    assert bad.requires_quarantine is True
    assert bad.findings[0].code is ConflictCode.COORDINATE_INVALID
