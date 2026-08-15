from registries.nngla.migration_architecture.plans import PLAN_CATALOGUE
from registries.nngla.migration_architecture.preview import PreviewService, TargetStateSnapshot
from registries.nngla.migration_architecture.selectors import Selector
from registries.nngla.migration_architecture.source_catalogue import SOURCE_DESCRIPTORS, SourceKind, load_source


def test_bundle16b_all_registered_sources_exist_are_hashed_and_preview_reads_only():
    for source_key, descriptor in SOURCE_DESCRIPTORS.items():
        snapshot = load_source(source_key)
        assert descriptor.path.is_file()
        assert len(snapshot.source_sha256) == 64
        assert snapshot.byte_size > 0
    assert all(plan.write_policy == "PREVIEW_ONLY" for plan in PLAN_CATALOGUE.values())


def test_bundle16b_supported_core_corpora_match_governed_repository_counts():
    assert len(load_source("places").records) == 700
    assert len(load_source("administrative-areas").records) == 192
    assert len(load_source("roads").records) == 900
    assert len(load_source("geographic-features").records) == 21
    assert len(load_source("geometry").records) == 21


def test_bundle16b_reference_catalogue_counts_do_not_create_physical_feature_ids():
    expected = {
        "names:hill": 280,
        "names:valley": 240,
        "names:river": 320,
        "names:forest": 260,
    }
    service = PreviewService()
    target = TargetStateSnapshot("npp_dev", "development", frozenset({"nngla_geographic_identity_places"}))
    for key, count in expected.items():
        snapshot = load_source(key)
        assert snapshot.descriptor.kind is SourceKind.REFERENCE_CATALOGUE
        preview = service.preview(key, target=target, repository_revision="bundle16b")
        assert preview.selected_count == count
        assert preview.proposed_canonical_ids == ()
        assert preview.database_writes == 0


def test_bundle16b_first_two_road_batches_propose_expected_non_overlapping_canonical_ids():
    service = PreviewService()
    target = TargetStateSnapshot("npp_dev", "development", frozenset({"nngla_geometry_roads_addresses"}))
    first = service.preview("roads", selector_override=Selector(limit=50), target=target, repository_revision="bundle16b")
    second = service.preview(
        "roads", selector_override=Selector(after_id="NG-RD-CAND-000050", limit=50),
        target=target, repository_revision="bundle16b",
    )
    assert first.proposed_canonical_ids[0] == "NG-RD-000001"
    assert first.proposed_canonical_ids[-1] == "NG-RD-000050"
    assert second.proposed_canonical_ids[0] == "NG-RD-000051"
    assert second.proposed_canonical_ids[-1] == "NG-RD-000100"
    assert not (set(first.proposed_canonical_ids) & set(second.proposed_canonical_ids))


def test_bundle16b_sovereign_boundary_uses_existing_world_geometry_capability_not_nngla_name_schema():
    service = PreviewService()
    not_ready = service.preview("sovereign-boundary", target=TargetStateSnapshot("npp_dev", "development"))
    ready = service.preview(
        "sovereign-boundary",
        target=TargetStateSnapshot("npp_dev", "development", frozenset({"world_geometry_authority"})),
        repository_revision="bundle16b",
    )
    assert not_ready.schema_ready is False
    assert ready.schema_ready is True
    assert ready.selected_count == 1
    assert ready.database_writes == 0


def test_bundle16b_current_core_plans_are_deterministic_and_zero_write():
    capabilities = frozenset({
        "world_geometry_authority",
        "nngla_geographic_identity_places",
        "nngla_geometry_roads_addresses",
        "nngla_cadastre_titles_state_land",
    })
    target = TargetStateSnapshot("npp_dev", "development", capabilities)
    service = PreviewService()
    for plan_id in ("places:city", "administrative-areas", "roads", "geographic-features", "geometry", "addresses", "parcels"):
        first = service.preview(plan_id, target=target, repository_revision="bundle16b")
        second = service.preview(plan_id, target=target, repository_revision="bundle16b")
        assert first.fingerprint == second.fingerprint
        assert first.database_writes == 0
