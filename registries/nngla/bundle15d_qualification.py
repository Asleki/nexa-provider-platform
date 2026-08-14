"""P006.7.9/P006.7.10 Bundle 15D qualification facade."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .publication_policy15d import PUBLIC_NAME_STATES, decide_place_visibility, title_public_visibility
from .read_models import NNGLAReadProjector
from .read_service import NNGLAReadService
from .sovereign_readiness import qualify_sovereign_spatial_readiness

QUALIFICATION_ID = "qualification:novegeo:nngla-bundle15d:v1"


@dataclass(frozen=True, slots=True)
class Bundle15DQualificationReceipt:
    qualification_id: str
    status: str
    findings: tuple[str, ...]
    source_place_count: int
    source_road_count: int
    canonical_place_count: int
    canonical_road_count: int
    published_place_count: int
    published_road_count: int
    published_address_count: int
    published_parcel_count: int
    sovereign_readiness_status: str
    live_database_migration_status: str
    semantic_checksum: str


def qualify_bundle15d(repository_root: str | Path) -> Bundle15DQualificationReceipt:
    findings: list[str] = []
    snapshot = NNGLAReadProjector().project()
    service = NNGLAReadService()
    readiness = qualify_sovereign_spatial_readiness(repository_root)
    places = snapshot.summary("PLACE")
    roads = snapshot.summary("ROAD")
    addresses = snapshot.summary("ADDRESS")
    parcels = snapshot.summary("PARCEL")

    if places.source_count != 700: findings.append(f"place-count:{places.source_count}")
    if roads.source_count != 900: findings.append(f"road-count:{roads.source_count}")
    if any(x.published_count for x in (places, roads, addresses, parcels)):
        findings.append("day-zero-public-domain-records-must-remain-empty")
    if service.status_dict()["databaseAuthority"] != "SERVER_SIDE_ONLY":
        findings.append("browser-database-authority-boundary")
    if title_public_visibility().public_eligible:
        findings.append("title-public-default-must-remain-restricted")
    gate_check = decide_place_visibility(naming_status_code="ACTIVE_OFFICIAL", spatial_assignment_status="AUTHORITATIVE_GEOMETRY_ASSIGNED")
    if gate_check.public_eligible or "NO_NNGLA_PUBLICATION_RECORD" not in gate_check.reasons:
        findings.append("bundle14c-publication-gate-not-enforced")
    if not {"GAZETTED", "ACTIVE_OFFICIAL", "HISTORIC", "PROTECTED"}.issubset(PUBLIC_NAME_STATES):
        findings.append("governed-public-name-states-incomplete")
    if readiness.status != "QUALIFIED":
        findings.extend(f"sovereign:{item}" for item in readiness.findings)

    return Bundle15DQualificationReceipt(
        QUALIFICATION_ID,
        "QUALIFIED" if not findings else "FAILED",
        tuple(findings),
        places.source_count,
        roads.source_count,
        places.canonical_count,
        roads.canonical_count,
        places.published_count,
        roads.published_count,
        addresses.published_count,
        parcels.published_count,
        readiness.status,
        readiness.live_database_migration_status,
        snapshot.semantic_checksum,
    )


__all__ = ["QUALIFICATION_ID", "Bundle15DQualificationReceipt", "qualify_bundle15d"]
