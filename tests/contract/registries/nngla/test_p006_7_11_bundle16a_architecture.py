from collections import Counter

from registries.nngla.bundle15a_source import (
    load_administrative_areas,
    load_feature_recognitions,
    load_places,
)
from registries.nngla.bundle15b_source import load_geometry_versions, load_road_candidates
from registries.nngla.migration_architecture import (
    ArchitectureAuditor,
    CanonicalIdentityAllocator,
    CanonicalObjectFamily,
    SourceIdentity,
)


def test_name_catalogue_and_all_four_nngla_schema_contracts_are_audited_read_only():
    report = ArchitectureAuditor().audit()
    assert len(report.name_migration_files) == 5
    assert len(report.nngla_schema_files) == 4
    assert {f.code for f in report.blocking_findings} == {
        "PLACE_CANONICAL_ID_REQUIRED",
        "ADMIN_CANONICAL_ID_REQUIRED",
    }


def test_bundle16a_records_candidate_to_canonical_gaps_without_mutating_locked_contracts():
    report = ArchitectureAuditor().audit()
    by_code = {f.code: f for f in report.findings}
    assert by_code["PLACE_CANONICAL_ID_REQUIRED"].subject == "geography.nngla_place_reference"
    assert by_code["ADMIN_CANONICAL_ID_REQUIRED"].subject == "geography.nngla_administrative_area"
    assert "additive migration architecture" in by_code["PLACE_CANONICAL_ID_REQUIRED"].detail
    assert "additive migration architecture" in by_code["ADMIN_CANONICAL_ID_REQUIRED"].detail


def test_current_700_place_corpus_can_receive_deterministic_canonical_place_ids_without_collision():
    allocator = CanonicalIdentityAllocator()
    proposals = tuple(
        allocator.propose(
            source=SourceIdentity(
                place.source_dataset_id,
                "1",
                place.source_place_code,
                None,
            ),
            object_family=CanonicalObjectFamily.PLACE,
        )
        for place in load_places()
    )
    assert len(proposals) == 700
    assert len({p.canonical_id for p in proposals}) == 700
    assert allocator.detect_proposal_collisions(proposals) == ()
    assert proposals[0].canonical_id == "NG-PLC-000001"
    assert proposals[-1].canonical_id == "NG-PLC-000700"


def test_current_192_administrative_candidates_can_receive_deterministic_canonical_ids_without_collision():
    allocator = CanonicalIdentityAllocator()
    proposals = tuple(
        allocator.propose(
            source=SourceIdentity(
                "dataset:novegeo:administrative-areas:v001:192",
                "1",
                area.source_record_id,
                area.administrative_candidate_id,
            ),
            object_family=CanonicalObjectFamily.ADMINISTRATIVE_AREA,
        )
        for area in load_administrative_areas()
    )
    assert len(proposals) == 192
    assert len({p.canonical_id for p in proposals}) == 192
    assert allocator.detect_proposal_collisions(proposals) == ()


def test_current_900_road_candidates_map_to_existing_canonical_road_namespace_without_collision():
    allocator = CanonicalIdentityAllocator()
    proposals = tuple(
        allocator.propose(
            source=SourceIdentity(
                "dataset:novegeo:roads:v001:900",
                "1",
                road.road_candidate_id,
                road.road_candidate_id,
            ),
            object_family=CanonicalObjectFamily.ROAD,
        )
        for road in load_road_candidates()
    )
    assert len(proposals) == 900
    assert len({p.canonical_id for p in proposals}) == 900
    assert allocator.detect_proposal_collisions(proposals) == ()
    assert proposals[0].canonical_id == "NG-RD-000001"
    assert proposals[-1].canonical_id == "NG-RD-000900"


def test_current_feature_and_geometry_ids_remain_distinct_namespaces():
    features = load_feature_recognitions()
    geometries = load_geometry_versions()
    assert len(features) == 21
    assert len(geometries) == 21
    assert all(f.recognition_id.startswith("NG-FEAT-") for f in features)
    assert all(g.geometry_id.startswith("NG-GEO-") for g in geometries)
    assert not ({f.recognition_id for f in features} & {g.geometry_id for g in geometries})


def test_current_place_types_are_explicitly_available_for_future_terminal_data_plans():
    counts = Counter(p.place_type_code for p in load_places())
    assert counts["CITY"] == 8
    assert counts["MUNICIPALITY"] == 24
    assert counts["TOWN"] == 120
    assert counts["VILLAGE"] == 240
