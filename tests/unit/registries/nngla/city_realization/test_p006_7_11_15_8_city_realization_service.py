from contextlib import contextmanager

from registries.nngla.city_realization.contracts import (
    CityExecutionResult,
    CityIdentity,
    CitySourceEvidence,
    ParentRegionAuthority,
    RealizationMethod,
    RealizedGeometry,
)
from registries.nngla.city_realization.service import GovernedCityRealizationService


CITY = "NG-ADM-000170"


def source_loader(_):
    geometry = {"type": "Polygon", "coordinates": [[[0,0],[1,0],[0,1],[0,0]]]}
    return CitySourceEvidence(
        CITY,"Port Meridian","NGR-08","NGC-08","candidate-8",
        "dataset:novegeo:administrative-boundaries","1","source.geojson",
        "a"*64,"b"*64,"POLYGON",geometry,
    )


class FakePostGIS:
    def load_city_identity(self, city_id):
        return CityIdentity(city_id, "Port Meridian", "NGR-08")
    def load_parent_region(self, region_code):
        return ParentRegionAuthority("NG-ADM-000008","Sabaran Gulf",region_code,"region-geometry:nngla:NG-ADM-000008:v1","c"*64)
    def realize(self, source, parent):
        geometry = source.geometry
        return RealizedGeometry(
            RealizationMethod.SOURCE_REUSE,"POLYGON",geometry,"d"*64,
            {"type":"Point","coordinates":[0.2,0.2]},100.0,0.0,0.0,
            100.0,0.0001,40.0,0.04,0.0,0.0,
        )


class FakeRepository:
    environment_name = "dev"
    database_name = "npp_dev"
    def __init__(self):
        self.current = None
        self.inserted_geometry = 0
        self.inserted_publication = 0
        self.persisted = 0
        self.verified = 0
        self.replay_value = None
    def current_city_authority(self, city_id): return self.current
    @contextmanager
    def transaction(self): yield self
    def replay(self, fingerprint): return self.replay_value
    def insert_geometry(self, plan): self.inserted_geometry += 1
    def insert_publication(self, plan): self.inserted_publication += 1
    def verify_public(self, plan): self.verified += 1
    def persist_execution(self, plan, **kwargs):
        self.persisted += 1
        return CityExecutionResult(
            "nnglarun:test",plan.fingerprint,plan.city_id,plan.city_geometry_id,
            plan.publication_id,self.database_name,self.environment_name,
            plan.repository_revision,kwargs["status"],False,
            kwargs["inserted_geometry_count"],kwargs["reused_geometry_count"],
        )


def test_preview_is_read_only_and_source_reuse_for_covered_city():
    repo = FakeRepository()
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    plan = service.preview(CITY)
    assert plan.city_id == CITY
    assert plan.parent_region_id == "NG-ADM-000008"
    assert plan.realization_method == "SOURCE_REUSE"
    assert plan.planned_action == "INSERT_AND_PUBLISH"
    assert repo.inserted_geometry == repo.inserted_publication == 0
    assert len(plan.fingerprint) == 64


def test_execute_replans_inside_transaction_and_requires_exact_approval():
    repo = FakeRepository()
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    plan = service.preview(CITY)
    result = service.execute(
        CITY,
        approved_fingerprint=plan.fingerprint,
        confirmation=plan.confirmation_token,
        submitter_actor_id="operator:a",
        approver_actor_id="operator:b",
    )
    assert result.status == "APPLIED"
    assert repo.inserted_geometry == 1
    assert repo.inserted_publication == 1
    assert repo.verified == 1
    assert repo.persisted == 1


def test_execute_rejects_same_submitter_and_approver_and_stale_fingerprint():
    repo = FakeRepository()
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    plan = service.preview(CITY)
    try:
        service.execute(CITY, approved_fingerprint=plan.fingerprint, confirmation=plan.confirmation_token, submitter_actor_id="same", approver_actor_id="same")
    except ValueError as exc:
        assert "different actors" in str(exc)
    else:
        raise AssertionError("same actor must fail")
    try:
        service.execute(CITY, approved_fingerprint="0"*64, confirmation=plan.confirmation_token, submitter_actor_id="a", approver_actor_id="b")
    except RuntimeError as exc:
        assert "fingerprint" in str(exc)
    else:
        raise AssertionError("stale fingerprint must fail")


def test_exact_existing_authority_changes_action_to_reuse_without_changing_governed_fingerprint():
    from registries.nngla.city_realization.contracts import CurrentCityAuthority
    repo = FakeRepository()
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    insert_plan = service.preview(CITY)
    repo.current = CurrentCityAuthority(
        insert_plan.city_geometry_id,
        insert_plan.geometry_sha256,
        insert_plan.parent_region_id,
        insert_plan.parent_region_geometry_id,
        insert_plan.parent_region_geometry_sha256,
        insert_plan.realization_method,
        insert_plan.realization_version,
        insert_plan.effective_date,
        insert_plan.publication_id,
        "PUBLISHED",
    )
    reuse_plan = service.preview(CITY)
    assert reuse_plan.planned_action == "REUSE"
    assert reuse_plan.fingerprint == insert_plan.fingerprint


def test_different_existing_authority_fails_closed_instead_of_superseding():
    from registries.nngla.city_realization.contracts import CurrentCityAuthority
    repo = FakeRepository()
    repo.current = CurrentCityAuthority(
        "city-geometry:nngla:NG-ADM-000170:v1",
        "e"*64,
        "NG-ADM-000008",
        "region-geometry:nngla:NG-ADM-000008:v1",
        "c"*64,
        "SOURCE_REUSE",
        1,
        "2026-08-29",
        "city-publication:nngla:NG-ADM-000170:v1",
        "PUBLISHED",
    )
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    try:
        service.preview(CITY)
    except RuntimeError as exc:
        assert "automatic supersession is prohibited" in str(exc)
    else:
        raise AssertionError("conflicting current authority must fail closed")


def test_withdrawn_existing_publication_is_not_silently_republished():
    from registries.nngla.city_realization.contracts import CurrentCityAuthority
    repo = FakeRepository()
    service = GovernedCityRealizationService(repo, FakePostGIS(), repository_revision="abc123", effective_date="2026-08-29", source_loader=source_loader)
    base = service.preview(CITY)
    repo.current = CurrentCityAuthority(
        base.city_geometry_id,
        base.geometry_sha256,
        base.parent_region_id,
        base.parent_region_geometry_id,
        base.parent_region_geometry_sha256,
        base.realization_method,
        base.realization_version,
        base.effective_date,
        base.publication_id,
        "WITHDRAWN",
    )
    try:
        service.preview(CITY)
    except RuntimeError as exc:
        assert "publication identity/status" in str(exc)
    else:
        raise AssertionError("withdrawn publication must require a future explicit governance path")
