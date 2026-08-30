from contextlib import contextmanager

from registries.nngla.city_containment_qualification.contracts import (
    ContainmentEvidence,
    QualificationBasis,
    QualificationStatus,
)
from registries.nngla.city_containment_qualification.service import GovernedCityContainmentQualificationService
from registries.nngla.city_realization.contracts import (
    CityIdentity,
    CitySourceEvidence,
    CurrentCityAuthority,
    ParentRegionAuthority,
)


CITY = "NG-ADM-000170"


def source_loader(_):
    return CitySourceEvidence(
        CITY, "Port Meridian", "NGR-08", "NGP-000609", "candidate-8",
        "dataset:novegeo:administrative-boundaries", "1", "source.geojson",
        "a" * 64, "b" * 64, "POLYGON",
        {"type":"Polygon","coordinates":[[[0,0],[1,0],[0,1],[0,0]]]},
    )


class FakePostGIS:
    def __init__(self, *, qualified=True, source_covered=True):
        self.qualified = qualified
        self.source_covered = source_covered
    def load_city_identity(self, city_id):
        return CityIdentity(city_id, "Port Meridian", "NGR-08")
    def load_parent_region(self, region_code):
        return ParentRegionAuthority(
            "NG-ADM-000008", "Sabaran Gulf", region_code,
            "region-geometry:nngla:NG-ADM-000008:v1", "c" * 64,
        )
    def evaluate(self, source, parent):
        status = QualificationStatus.QUALIFIED if self.qualified else QualificationStatus.REJECTED
        basis = QualificationBasis.STRICT_SOURCE_COVERED if self.qualified else QualificationBasis.REJECTED_RESIDUE_EXCEEDS_POLICY
        return ContainmentEvidence(
            True, True, "POLYGON", self.source_covered, 100.0, 0.0, 0.0,
            True, True, "POLYGON", self.source_covered, 100.0,
            0.0 if self.qualified else 1.0,
            0.0 if self.qualified else 0.01,
            40.0, True,
            source.geometry, {"type":"Point","coordinates":[0.2,0.2]},
            "d" * 64,
            "SOURCE_REUSE" if self.source_covered else "PARENT_CONTAINED_NORMALIZATION",
            0.0, 0.0, status, basis,
        )


class FakeRepository:
    environment_name = "dev"
    database_name = "npp_dev"
    def __init__(self):
        self.current = None
        self.current_q = None
        self.replay_value = None
        self.inserted_q = 0
        self.inserted_g = 0
        self.inserted_p = 0
        self.verified_q = 0
        self.verified_p = 0
        self.persisted = 0
    def current_city_authority(self, city_id): return self.current
    def current_qualification(self, city_id): return self.current_q
    @contextmanager
    def transaction(self): yield self
    def replay(self, fingerprint): return self.replay_value
    def insert_qualification(self, plan): self.inserted_q += 1
    def insert_geometry(self, plan): self.inserted_g += 1
    def insert_publication(self, plan): self.inserted_p += 1
    def verify_qualification(self, plan): self.verified_q += 1
    def verify_public(self, plan): self.verified_p += 1
    def persist_execution(self, plan, **kwargs):
        self.persisted += 1
        return {"status": kwargs["status"], "city": plan.city_id}


def service(repo, postgis=None):
    return GovernedCityContainmentQualificationService(
        repo,
        postgis or FakePostGIS(),
        repository_revision="abc123",
        effective_date="2026-08-30",
        source_loader=source_loader,
    )


def test_new_qualified_city_plans_insert_and_publish_and_preview_is_read_only():
    repo = FakeRepository()
    plan = service(repo).preview(CITY)
    assert plan.planned_action == "INSERT_AND_PUBLISH"
    assert plan.qualification_status == "QUALIFIED"
    assert repo.inserted_q == repo.inserted_g == repo.inserted_p == 0


def test_existing_port_meridian_is_attested_without_geometry_or_publication_rewrite():
    repo = FakeRepository()
    initial = service(repo).preview(CITY)
    repo.current = CurrentCityAuthority(
        initial.city_geometry_id, initial.geometry_sha256, initial.parent_region_id,
        initial.parent_region_geometry_id, initial.parent_region_geometry_sha256,
        initial.realization_method, initial.realization_version, initial.effective_date,
        initial.publication_id, "PUBLISHED",
    )
    attestation = service(repo).preview(CITY)
    assert attestation.planned_action == "ATTEST_EXISTING"
    result = service(repo).execute(
        CITY,
        approved_fingerprint=attestation.fingerprint,
        confirmation=attestation.confirmation_token,
        submitter_actor_id="npp-admin",
        approver_actor_id="asleki-admin",
    )
    assert result["status"] == "APPLIED"
    assert repo.inserted_q == 1
    assert repo.inserted_g == 0
    assert repo.inserted_p == 0
    assert repo.verified_q == 1
    assert repo.verified_p == 1


def test_rejected_city_persists_qualification_but_never_geometry_or_publication():
    repo = FakeRepository()
    svc = service(repo, FakePostGIS(qualified=False, source_covered=False))
    plan = svc.preview(CITY)
    assert plan.planned_action == "QUALIFY_ONLY"
    assert not plan.public_ready
    svc.execute(
        CITY,
        approved_fingerprint=plan.fingerprint,
        confirmation=plan.confirmation_token,
        submitter_actor_id="npp-admin",
        approver_actor_id="asleki-admin",
    )
    assert repo.inserted_q == 1
    assert repo.inserted_g == 0
    assert repo.inserted_p == 0
    assert repo.verified_q == 1
    assert repo.verified_p == 0


def test_actor_separation_and_stale_approval_remain_fail_closed():
    repo = FakeRepository()
    svc = service(repo)
    plan = svc.preview(CITY)
    try:
        svc.execute(
            CITY,
            approved_fingerprint=plan.fingerprint,
            confirmation=plan.confirmation_token,
            submitter_actor_id="same",
            approver_actor_id="same",
        )
    except ValueError as exc:
        assert "different actors" in str(exc)
    else:
        raise AssertionError("same actor must fail")

    try:
        svc.execute(
            CITY,
            approved_fingerprint="0" * 64,
            confirmation=plan.confirmation_token,
            submitter_actor_id="npp-admin",
            approver_actor_id="asleki-admin",
        )
    except RuntimeError as exc:
        assert "fingerprint" in str(exc)
    else:
        raise AssertionError("stale fingerprint must fail")


def test_existing_city_can_be_attested_on_later_qualification_date_without_rewriting_geometry_effective_date():
    repo = FakeRepository()
    initial = service(repo).preview(CITY)
    repo.current = CurrentCityAuthority(
        initial.city_geometry_id,
        initial.geometry_sha256,
        initial.parent_region_id,
        initial.parent_region_geometry_id,
        initial.parent_region_geometry_sha256,
        initial.realization_method,
        initial.realization_version,
        "2026-08-29",
        initial.publication_id,
        "PUBLISHED",
    )
    plan = service(repo).preview(CITY)
    assert plan.effective_date == "2026-08-30"
    assert plan.planned_action == "ATTEST_EXISTING"
