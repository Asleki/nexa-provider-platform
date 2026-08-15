import pytest

from registries.nngla.migration_architecture.plans import PLAN_CATALOGUE, PlanPurpose, get_plan
from registries.nngla.migration_architecture.preview import PreviewService, TargetStateSnapshot
from registries.nngla.migration_architecture.selectors import Selector, SelectorKind, select_records
from registries.nngla.migration_architecture.source_catalogue import SourceKind, load_source


def test_plan_catalogue_exposes_required_terminal_domain_families():
    required = {
        "sovereign-boundary", "places:city", "places:municipality", "places:town", "places:village",
        "administrative-areas", "roads", "geographic-features", "geometry", "survey-control",
        "addresses", "parcels", "titles", "state-land", "names:hill", "names:valley", "names:river", "names:forest",
    }
    assert required <= set(PLAN_CATALOGUE)
    assert all(plan.write_policy == "PREVIEW_ONLY" for plan in PLAN_CATALOGUE.values())


def test_reference_name_plans_cannot_be_confused_with_canonical_feature_plans():
    hill = get_plan("names:hill")
    assert hill.purpose is PlanPurpose.REFERENCE_CATALOGUE
    assert load_source(hill.source_key).descriptor.kind is SourceKind.REFERENCE_CATALOGUE
    assert get_plan("geographic-features").purpose is PlanPurpose.CANONICAL_OBJECT


def test_current_place_type_plans_select_exact_governed_counts():
    service = PreviewService()
    target = TargetStateSnapshot("npp_dev", "development", frozenset({"nngla_geographic_identity_places"}))
    expected = {"places:city": 8, "places:municipality": 24, "places:town": 120, "places:village": 240}
    for plan_id, count in expected.items():
        preview = service.preview(plan_id, target=target, repository_revision="test")
        assert preview.selected_count == count
        assert preview.database_writes == 0
        assert preview.execution_ready is True


def test_road_ordered_slice_is_stable_and_supports_next_batch_without_random_sampling():
    source = load_source("roads")
    first = select_records(source.records, Selector(limit=50))
    second = select_records(source.records, Selector(after_id=first[-1].source_id, limit=50))
    assert len(first) == len(second) == 50
    assert first[0].source_id == "NG-RD-CAND-000001"
    assert first[-1].source_id == "NG-RD-CAND-000050"
    assert second[0].source_id == "NG-RD-CAND-000051"
    assert second[-1].source_id == "NG-RD-CAND-000100"
    assert not ({r.source_id for r in first} & {r.source_id for r in second})


def test_exact_id_selector_fails_closed_when_requested_id_is_missing():
    source = load_source("roads")
    with pytest.raises(ValueError, match="missing"):
        select_records(source.records, Selector(SelectorKind.EXACT_IDS, exact_ids=("NG-RD-CAND-999999",)))


def test_preview_fingerprint_is_deterministic_and_changes_when_selection_changes():
    service = PreviewService()
    target = TargetStateSnapshot("npp_dev", "development", frozenset({"nngla_geometry_roads_addresses"}))
    a = service.preview("roads", selector_override=Selector(limit=50), target=target, repository_revision="abc")
    b = service.preview("roads", selector_override=Selector(limit=50), target=target, repository_revision="abc")
    c = service.preview("roads", selector_override=Selector(limit=51), target=target, repository_revision="abc")
    assert a.fingerprint == b.fingerprint
    assert a.fingerprint != c.fingerprint
    assert a.database_writes == b.database_writes == c.database_writes == 0


def test_preview_detects_schema_prerequisite_without_writing():
    preview = PreviewService().preview("places:city", target=TargetStateSnapshot("npp_dev", "development"))
    assert preview.schema_ready is False
    assert preview.execution_ready is False
    assert preview.database_writes == 0
    assert preview.qualification_counts == {"QUALIFIED": 8}


def test_preview_marks_governed_empty_address_register_as_valid_empty_source():
    target = TargetStateSnapshot("npp_dev", "development", frozenset({"nngla_geometry_roads_addresses"}))
    preview = PreviewService().preview("addresses", target=target, repository_revision="abc")
    assert preview.source_count == 0
    assert preview.selected_count == 0
    assert preview.qualification_counts == {"EMPTY_GOVERNED_SOURCE": 1}
    assert preview.execution_ready is True
    assert preview.database_writes == 0


def test_preview_refuses_target_canonical_id_collision():
    target = TargetStateSnapshot(
        "npp_dev", "development", frozenset({"nngla_geographic_identity_places"}), frozenset({"NG-PLC-000001"})
    )
    preview = PreviewService().preview("places:city", target=target, repository_revision="abc")
    assert preview.execution_ready is False
