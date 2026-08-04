"""
NexiLabs NoveGeo PWA
File: pwa_roadmap_data.py

Authoritative structured roadmap data for the AWS-hosted NexiLabs NoveGeo PWA.

The current roadmap is intentionally limited to:
- installable PWA foundations;
- AWS hosting and delivery;
- NexiLabs brand integration;
- the NoveGeo map, coordinates, terrain, hydrology, climate and vegetation;
- map interaction and simulation-state presentation;
- a secure future API boundary to NPP and PostgreSQL.

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

ROADMAP_VERSION: Final[str] = "0.1.0"
ROADMAP_TITLE: Final[str] = "NexiLabs NoveGeo PWA — AWS Map Foundation Roadmap"
ROADMAP_START: Final[str] = "P001"
ROADMAP_END: Final[str] = "P012.7"
ROADMAP_BOUNDARIES: Final[Mapping[str, str]] = MappingProxyType({
    "runtime_host": "AWS",
    "initial_product_scope": "NoveGeo map and world visualisation",
    "database_access": "Browser to secured NPP/AWS API only; never direct PostgreSQL",
    "cross_roadmap_rule": "PWA completion may provide evidence but never automatically completes an NPP record",
})

_ROADMAP_OUTLINE: Final[str] = r"""
P|P001|NexiLabs PWA Project Foundation
C|P001.1|PWA Scope and Product Boundary
P|P001.2|Repository Placement and Naming
P|P001.3|Frontend Directory Foundation
P|P001.4|Python Roadmap Governance Files
P|P001.5|Canonical PWA Roadmap Dataset
P|P001.6|Roadmap CLI and Verification
P|P001.7|GitHub Markdown Roadmap Frontend
P|P001.8|Project Foundation Tests
P|P002|NexiLabs Brand Integration
P|P002.1|Canonical Brand Asset Location
P|P002.2|Brand Asset Inventory Validation
P|P002.3|Primary Logo Integration
P|P002.4|Responsive Wordmark Integration
P|P002.5|Favicon Integration
P|P002.6|Apple Touch Icon Integration
P|P002.7|PWA Icon Integration
P|P002.8|Social Preview Integration
P|P002.9|Brand Token Stylesheet Integration
P|P003|HTML, Metadata and Installable PWA Foundation
P|P003.1|HTML Application Shell
P|P003.2|Document Language and Character Encoding
P|P003.3|Viewport and Mobile Presentation
P|P003.4|Title and Description Metadata
P|P003.5|Canonical URL Metadata
P|P003.6|Open Graph Metadata
P|P003.7|Social Card Metadata
P|P003.8|Web App Manifest
P|P003.9|Browser Configuration Metadata
P|P003.10|Robots and Sitemap Metadata
P|P003.11|Install Prompt Readiness
P|P003.12|Metadata and Installation Tests
P|P004|AWS Hosting and Deployment Foundation
P|P004.1|AWS Hosting Architecture Decision
P|P004.2|Environment Separation
P|P004.3|Static Build Output Contract
P|P004.4|Amazon S3 Hosting Foundation
P|P004.5|Amazon CloudFront Distribution
P|P004.6|HTTPS Certificate Foundation
P|P004.7|Domain and DNS Integration Boundary
P|P004.8|Cache-Control Policy
P|P004.9|Deployment Automation
P|P004.10|Rollback and Version Recovery
P|P004.11|AWS Deployment Qualification
P|P005|Frontend Architecture and Runtime Configuration
P|P005.1|Application Bootstrap
P|P005.2|Module Boundary Convention
P|P005.3|Runtime Configuration Contract
P|P005.4|Development Environment Configuration
P|P005.5|Simulation Environment Configuration
P|P005.6|Production Environment Configuration
P|P005.7|Feature Capability Discovery
P|P005.8|Error Boundary Foundation
P|P005.9|Logging Boundary
P|P005.10|Architecture Tests
P|P006|NoveGeo World Coordinate Foundation
P|P006.1|World Boundary Contract
P|P006.2|Coordinate Reference System
P|P006.3|Latitude and Longitude Grid
P|P006.4|Equator Reference
P|P006.5|Map Projection Selection
P|P006.6|World Extent Validation
P|P006.7|Coordinate Conversion Utilities
P|P006.8|Viewport-to-Coordinate Mapping
P|P006.9|Coordinate Display Interface
P|P006.10|Coordinate Foundation Tests
P|P007|NoveGeo Terrain and Elevation Presentation
P|P007.1|Terrain Data Contract
P|P007.2|Elevation Range Policy
P|P007.3|Mountain and Highland Layers
P|P007.4|Valley and Basin Layers
P|P007.5|Plateau and Plain Layers
P|P007.6|Slope Classification
P|P007.7|Relief Shading
P|P007.8|Terrain Legend
P|P007.9|Terrain Layer Controls
P|P007.10|Terrain Presentation Tests
P|P008|NoveGeo Hydrology, Climate and Vegetation Layers
P|P008.1|Hydrology Data Contract
P|P008.2|River and Stream Layers
P|P008.3|Lake and Reservoir Layers
P|P008.4|Watershed and Drainage Boundaries
P|P008.5|Climate Zone Contract
P|P008.6|Temperature Presentation
P|P008.7|Rainfall Presentation
P|P008.8|Windward and Leeward Effects
P|P008.9|Vegetation Classification
P|P008.10|Desert and Arid Zone Presentation
P|P008.11|Seasonal Layer State
P|P008.12|Environmental Layer Tests
P|P009|NoveGeo Map Interaction and Navigation
P|P009.1|Map Pan Interaction
P|P009.2|Map Zoom Interaction
P|P009.3|Touch Gesture Support
P|P009.4|Keyboard Navigation
P|P009.5|Layer Visibility Controls
P|P009.6|Map Legend and Scale
P|P009.7|Coordinate Search
P|P009.8|Location Selection
P|P009.9|Map History Navigation
P|P009.10|Responsive Map Layout
P|P009.11|Interaction and Navigation Tests
P|P010|Simulation Time and Dynamic World State Presentation
P|P010.1|Simulation Clock Contract
P|P010.2|One-to-One Time Ratio Presentation
P|P010.3|Simulation Date Display
P|P010.4|World State Snapshot Contract
P|P010.5|Environmental State Refresh
P|P010.6|Dynamic Layer Update
P|P010.7|Paused and Running States
P|P010.8|State Change Indicators
P|P010.9|Dynamic World Presentation Tests
P|P011|Data Access and PostgreSQL Integration Boundary
P|P011.1|Browser-to-API Security Boundary
P|P011.2|No Direct PostgreSQL Access Rule
P|P011.3|NPP Query API Contract
P|P011.4|Read-Only Data Access Foundation
P|P011.5|Name Catalogue Browser Reservation
P|P011.6|Filtered Name Search Reservation
P|P011.7|Runtime-Mode Separation in Responses
P|P012|Testing, Security, Performance and Alpha Release
P|P012.1|Frontend Unit Testing
P|P012.2|PWA Installation Testing
P|P012.3|Offline Shell Testing
P|P012.4|Accessibility Qualification
P|P012.5|Browser Security Headers
P|P012.6|Performance Budget
P|P012.7|AWS Alpha Release Qualification
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
