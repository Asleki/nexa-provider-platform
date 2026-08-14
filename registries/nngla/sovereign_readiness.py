"""P006.7.10 cross-bundle sovereign NNGLA readiness qualification."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .bundle15a_qualification import qualify_bundle15a
from .bundle15b_qualification import qualify_bundle15b
from .bundle15c_qualification import qualify_bundle15c
from .foundation_qualification import qualify_nngla_foundation
from .read_models import NNGLAReadProjector
from .publication_policy15d import title_public_visibility


@dataclass(frozen=True, slots=True)
class SovereignSpatialReadinessReceipt:
    qualification_id: str
    status: str
    findings: tuple[str, ...]
    authority_readiness: str
    source_integrity_readiness: str
    schema_readiness: str
    read_model_readiness: str
    publication_readiness: str
    privacy_readiness: str
    pwa_consumer_boundary: str
    live_database_migration_status: str
    place_population_state: str
    road_population_state: str
    address_population_state: str
    parcel_population_state: str
    title_population_state: str
    state_land_population_state: str
    semantic_checksum: str


def qualify_sovereign_spatial_readiness(repository_root: str | Path) -> SovereignSpatialReadinessReceipt:
    root = Path(repository_root)
    findings: list[str] = []

    foundation = qualify_nngla_foundation(root)
    bundle15a = qualify_bundle15a()
    bundle15b = qualify_bundle15b()
    bundle15c = qualify_bundle15c()
    for receipt, label, success in (
        (foundation, "foundation", "PASSED"),
        (bundle15a, "bundle15a", "QUALIFIED"),
        (bundle15b, "bundle15b", "QUALIFIED"),
        (bundle15c, "bundle15c", "QUALIFIED"),
    ):
        if receipt.status != success:
            findings.append(f"{label}-qualification:{receipt.status}")

    snapshot = NNGLAReadProjector().project()
    expected = {
        "PLACE": 700,
        "ADMINISTRATIVE_AREA": 192,
        "GEOGRAPHIC_FEATURE": 21,
        "ROAD": 900,
        "ADDRESS": 0,
        "PARCEL": 0,
    }
    for family, count in expected.items():
        summary = snapshot.summary(family)
        if summary.source_count != count:
            findings.append(f"{family.lower()}-known-count:{summary.source_count}")

    # Day-Zero sources are intentionally not public/map-ready. Publication work
    # must not silently legalize or spatialize provisional records.
    for family in ("PLACE", "ADMINISTRATIVE_AREA", "GEOGRAPHIC_FEATURE", "ROAD", "ADDRESS", "PARCEL"):
        summary = snapshot.summary(family)
        if summary.published_count != 0 or summary.map_renderable_count != 0:
            findings.append(f"{family.lower()}-unexpected-publication:{summary.published_count}:{summary.map_renderable_count}")

    if title_public_visibility().public_eligible:
        findings.append("title-publication-must-remain-restricted")
    if bundle15c.title_bootstrap_count or bundle15c.state_land_bootstrap_count:
        findings.append("legal-land-day-zero-registers-changed")

    return SovereignSpatialReadinessReceipt(
        qualification_id="qualification:novegeo:nngla-sovereign-spatial-readiness:v1",
        status="QUALIFIED" if not findings else "FAILED",
        findings=tuple(findings),
        authority_readiness="READY" if foundation.status == "PASSED" else "FAILED",
        source_integrity_readiness="READY" if not findings else "CHECK_FINDINGS",
        schema_readiness="READY" if all(x.status == "QUALIFIED" for x in (bundle15a, bundle15b, bundle15c)) else "FAILED",
        read_model_readiness="READY",
        publication_readiness="READY_POLICY_NO_ELIGIBLE_DOMAIN_RECORDS",
        privacy_readiness="READY_RESTRICTED_TITLE_DEFAULT",
        pwa_consumer_boundary="READ_ONLY_API_NO_DATABASE_AUTHORITY",
        live_database_migration_status="NOT_EXECUTED",
        place_population_state=snapshot.summary("PLACE").population_state,
        road_population_state=snapshot.summary("ROAD").population_state,
        address_population_state=snapshot.summary("ADDRESS").population_state,
        parcel_population_state=snapshot.summary("PARCEL").population_state,
        title_population_state="EMPTY_DAY_ZERO" if bundle15c.title_bootstrap_count == 0 else "POPULATED",
        state_land_population_state="EMPTY_DAY_ZERO" if bundle15c.state_land_bootstrap_count == 0 else "POPULATED",
        semantic_checksum=snapshot.semantic_checksum,
    )


__all__ = ["SovereignSpatialReadinessReceipt", "qualify_sovereign_spatial_readiness"]
