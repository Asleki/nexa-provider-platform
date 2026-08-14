from registries.nngla.publication_policy15d import (
    PublicReadVisibility,
    decide_place_visibility,
    decide_road_visibility,
    title_public_visibility,
)
from registries.nngla.read_models import MemoryNNGLAReadRepository, NNGLAReadProjector
from registries.nngla.read_service import NNGLAReadService


def test_p006_7_9_projects_known_registry_population_without_fabricating_public_records():
    snapshot = NNGLAReadProjector().project()
    assert snapshot.summary("PLACE").source_count == 700
    assert snapshot.summary("ADMINISTRATIVE_AREA").source_count == 192
    assert snapshot.summary("GEOGRAPHIC_FEATURE").source_count == 21
    assert snapshot.summary("ROAD").source_count == 900
    assert snapshot.summary("ADDRESS").source_count == 0
    assert snapshot.summary("PARCEL").source_count == 0
    assert all(summary.canonical_count == 0 for summary in snapshot.summaries)
    assert all(summary.published_count == 0 for summary in snapshot.summaries)
    assert all(summary.map_renderable_count == 0 for summary in snapshot.summaries)
    assert snapshot.summary("TITLE").source_count == 0
    assert snapshot.summary("STATE_LAND").source_count == 0


def test_p006_7_9_unmapped_proposed_places_are_registry_known_but_not_public_or_map_renderable():
    snapshot = NNGLAReadProjector().project()
    place = next(item for item in snapshot.items if item.family == "PLACE")
    assert place.subject_id == "NGP-000001"
    assert place.public_eligible is False
    assert place.map_renderable is False
    assert place.geometry_reference is None
    assert "NAME_NOT_PUBLIC" in place.visibility_reasons
    assert "NO_AUTHORITATIVE_SPATIAL_ASSIGNMENT" in place.visibility_reasons


def test_p006_7_9_reserved_unmapped_roads_never_become_public_by_projection():
    snapshot = NNGLAReadProjector().project()
    road = next(item for item in snapshot.items if item.family == "ROAD")
    assert road.public_eligible is False
    assert road.map_renderable is False
    assert "ROAD_NOT_OPERATIONALLY_ACTIVE" in road.visibility_reasons
    assert "ROAD_NOT_AUTHORITATIVELY_MAPPED" in road.visibility_reasons


def test_p006_7_9_public_policy_requires_both_legal_name_and_spatial_assignment():
    proposed = decide_place_visibility(naming_status_code="PROPOSED", spatial_assignment_status="UNMAPPED_PENDING_ASSOCIATION")
    assert proposed.visibility is PublicReadVisibility.INTERNAL
    assert proposed.public_eligible is False
    without_publication = decide_place_visibility(naming_status_code="ACTIVE_OFFICIAL", spatial_assignment_status="AUTHORITATIVE_GEOMETRY_ASSIGNED")
    assert without_publication.public_eligible is False
    assert "NO_NNGLA_PUBLICATION_RECORD" in without_publication.reasons
    eligible = decide_place_visibility(naming_status_code="ACTIVE_OFFICIAL", spatial_assignment_status="AUTHORITATIVE_GEOMETRY_ASSIGNED", published_through_gate=True)
    assert eligible.public_eligible is True
    assert eligible.map_renderable is True


def test_p006_7_9_read_models_are_deterministic_and_rebuildable():
    projector = NNGLAReadProjector()
    first = projector.project()
    second = projector.project()
    assert first.semantic_checksum == second.semantic_checksum
    repository = MemoryNNGLAReadRepository()
    rebuilt = projector.rebuild(repository)
    assert repository.get().semantic_checksum == rebuilt.semantic_checksum == first.semantic_checksum


def test_p006_7_9_public_service_exposes_only_public_items_and_keeps_title_restricted():
    service = NNGLAReadService()
    places = service.list_public("PLACE")
    assert places["sourceCount"] == 700
    assert places["canonicalCount"] == 0
    assert places["publishedCount"] == 0
    assert places["count"] == 0
    assert places["items"] == []
    assert service.status_dict()["databaseAuthority"] == "SERVER_SIDE_ONLY"
    assert title_public_visibility().public_eligible is False
    assert title_public_visibility().visibility is PublicReadVisibility.RESTRICTED
