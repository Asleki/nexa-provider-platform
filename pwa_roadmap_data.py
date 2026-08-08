"""
NexiLabs NoveGeo PWA
File: pwa_roadmap_data.py

Authoritative structured roadmap data for the AWS-hosted NexiLabs NoveGeo PWA.

The revised roadmap is capability-oriented and intentionally limited to:
- a small consolidated documentation and governance foundation;
- executable application, branding, installation and offline capability;
- the NoveGeo map, coordinates, terrain, water, climate and vegetation;
- interaction, dynamic simulation-state presentation and AWS delivery;
- a secured NPP API boundary and an initial read-only Name Catalogue interface.

It does not claim that National, School, Business, Health or Financial
registries already exist. Those interfaces are deliberately deferred.
"""
from __future__ import annotations

from hashlib import sha256
from types import MappingProxyType
from typing import Final, Iterable, Mapping

STATUS_COMPLETED: Final[str] = "COMPLETED"
STATUS_PLANNED: Final[str] = "PLANNED"
ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({STATUS_COMPLETED, STATUS_PLANNED})

ROADMAP_VERSION: Final[str] = "0.2.0"
ROADMAP_TITLE: Final[str] = "NexiLabs NoveGeo PWA — AWS Map Foundation Roadmap"
ROADMAP_START: Final[str] = "P001"
ROADMAP_END: Final[str] = "P008.6"
ROADMAP_BOUNDARIES: Final[Mapping[str, str]] = MappingProxyType({
    "runtime_host": "AWS",
    "initial_product_scope": "NoveGeo map and world visualisation",
    "database_access": "Browser to secured NPP/AWS API only; never direct PostgreSQL",
    "cross_roadmap_rule": "PWA completion may provide evidence but never automatically completes an NPP record",
})

_ROADMAP_OUTLINE: Final[str] = r"""
C|P001|NexiLabs PWA Project Foundation
C|P001.1|PWA Scope and Product Boundary
C|P001.2|Repository, Frontend and Roadmap Governance
C|P001.3|Foundation Verification and Operating Rules
C|P002|Application Shell and Brand Integration
C|P002.1|Executable Frontend Application Skeleton
C|P002.2|Application Bootstrap and Health State
C|P002.3|Canonical NexiLabs Brand Consumption
C|P002.4|Responsive Base Layout and Styling
C|P002.5|Application Shell Integration Tests
C|P003|Installable and Offline PWA
C|P003.1|Web App Manifest and Install Metadata
C|P003.2|Service Worker Registration and Lifecycle
C|P003.3|Offline Application Shell Cache
C|P003.4|Update, Recovery and Cache Versioning
C|P003.5|Installation and Offline Qualification
C|P004|NoveGeo World Geometry and Map Core
C|P004.1|Governed World Boundary Dataset
C|P004.2|Coordinate Reference and Projection Engine
C|P004.3|Map Canvas and Viewport Renderer
C|P004.4|Latitude, Longitude and Equator Overlay
C|P004.5|World Extent and Coordinate Validation
C|P004.6|Map Core Integration Tests
P|P005|Terrain, Water, Climate and Vegetation
C|P005.1|Terrain and Elevation Data Engine
C|P005.2|Mountain, Valley, Plain and Plateau Layers
C|P005.3|River, Lake and Drainage Layers
C|P005.4|Climate, Rainfall and Wind Effects
P|P005.5|Vegetation and Arid-Zone Layers
P|P005.6|Environmental Layer Integration Tests
P|P006|Map Interaction and Dynamic World State
P|P006.1|Pan, Zoom, Touch and Keyboard Navigation
P|P006.2|Layer Controls, Legend and Scale
P|P006.3|Coordinate Search and Location Selection
P|P006.4|One-to-One Simulation Clock Presentation
P|P006.5|Versioned Dynamic World-State Updates
P|P006.6|Interaction and Dynamic-State Tests
P|P007|AWS Hosting and Release Operations
P|P007.1|AWS Static Hosting and Build Output
P|P007.2|CloudFront, HTTPS and Domain Delivery
P|P007.3|Environment Configuration and Security Headers
P|P007.4|Deployment Automation and Rollback
P|P007.5|AWS Deployment Qualification
P|P008|Secure NPP Data Access and Alpha Qualification
P|P008.1|Browser-to-API Client Boundary
P|P008.2|Runtime-Safe Read-Only Query Client
P|P008.3|Name Catalogue Read Interface
P|P008.4|Alphabet, Search and Sex-Usage Filters
P|P008.5|Privacy, Accessibility and Performance Qualification
P|P008.6|NoveGeo PWA Alpha Release
"""

_STATUS_CODE_MAP: Final[Mapping[str, str]] = MappingProxyType({
    "C": STATUS_COMPLETED,
    "P": STATUS_PLANNED,
})


def _stable_record_id(semantic_path: str) -> str:
    digest = sha256(semantic_path.encode("utf-8")).hexdigest()[:20]
    return f"nxl-pwa-rm-{digest}"


def _parse_outline(lines: Iterable[str]) -> tuple[Mapping[str, object], ...]:
    records: list[dict[str, object]] = []
    title_by_number: dict[str, str] = {}

    for sequence, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ValueError(f"invalid roadmap row: {line!r}")
        status_code, number, title = (part.strip() for part in parts)
        if status_code not in _STATUS_CODE_MAP:
            raise ValueError(f"unsupported roadmap status code: {status_code!r}")
        if number in title_by_number:
            raise ValueError(f"duplicate roadmap number: {number}")

        depth = number.count(".")
        parent_number = number.rsplit(".", 1)[0] if depth else None
        if parent_number is not None and parent_number not in title_by_number:
            raise ValueError(f"missing parent {parent_number} for {number}")

        title_by_number[number] = title
        semantic_titles = [title]
        ancestor = parent_number
        while ancestor is not None:
            semantic_titles.append(title_by_number[ancestor])
            ancestor = ancestor.rsplit(".", 1)[0] if "." in ancestor else None
        semantic_path = " / ".join(reversed(semantic_titles))

        records.append({
            "number": number,
            "title": title,
            "status": _STATUS_CODE_MAP[status_code],
            "sequence": len(records) + 1,
            "depth": depth,
            "parent_number": parent_number,
            "record_id": _stable_record_id(semantic_path),
            "semantic_path": semantic_path,
            "priority": "NORMAL",
            "verification_state": "UNVERIFIED",
            "dependencies": (),
            "cross_roadmap_refs": (),
            "started_date": None,
            "completed_date": None,
            "commit_hash": None,
            "passing_tests": None,
            "notes": (),
            "test_information": (),
        })

    return tuple(MappingProxyType(record) for record in records)


MILESTONES: Final[tuple[Mapping[str, object], ...]] = _parse_outline(
    _ROADMAP_OUTLINE.splitlines()
)
ROOT_MILESTONES: Final[tuple[Mapping[str, object], ...]] = tuple(
    record for record in MILESTONES if record["parent_number"] is None
)
TOTAL_MILESTONES: Final[int] = len(MILESTONES)
COMPLETED_MILESTONES: Final[int] = sum(
    record["status"] == STATUS_COMPLETED for record in MILESTONES
)
PLANNED_MILESTONES: Final[int] = sum(
    record["status"] == STATUS_PLANNED for record in MILESTONES
)

_BY_NUMBER: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {str(record["number"]): record for record in MILESTONES}
)
_BY_RECORD_ID: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {str(record["record_id"]): record for record in MILESTONES}
)


def get_milestone(identifier: str) -> Mapping[str, object]:
    try:
        return _BY_NUMBER[identifier]
    except KeyError:
        try:
            return _BY_RECORD_ID[identifier]
        except KeyError as exc:
            raise KeyError(f"roadmap milestone was not found: {identifier}") from exc


def get_children(number: str) -> tuple[Mapping[str, object], ...]:
    return tuple(record for record in MILESTONES if record["parent_number"] == number)


def get_descendants(number: str) -> tuple[Mapping[str, object], ...]:
    prefix = number + "."
    return tuple(
        record for record in MILESTONES
        if str(record["number"]).startswith(prefix)
    )


def roadmap_summary() -> Mapping[str, object]:
    return MappingProxyType({
        "title": ROADMAP_TITLE,
        "version": ROADMAP_VERSION,
        "start": ROADMAP_START,
        "end": ROADMAP_END,
        "total": TOTAL_MILESTONES,
        "completed": COMPLETED_MILESTONES,
        "planned": PLANNED_MILESTONES,
        "roots": len(ROOT_MILESTONES),
        "boundaries": dict(ROADMAP_BOUNDARIES),
    })


__all__ = [
    "ALLOWED_STATUSES",
    "COMPLETED_MILESTONES",
    "MILESTONES",
    "PLANNED_MILESTONES",
    "ROADMAP_BOUNDARIES",
    "ROADMAP_END",
    "ROADMAP_START",
    "ROADMAP_TITLE",
    "ROADMAP_VERSION",
    "ROOT_MILESTONES",
    "STATUS_COMPLETED",
    "STATUS_PLANNED",
    "TOTAL_MILESTONES",
    "get_children",
    "get_descendants",
    "get_milestone",
    "roadmap_summary",
]
