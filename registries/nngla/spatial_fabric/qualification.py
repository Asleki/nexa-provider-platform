"""Bundle 17A source and topology qualification facade."""
from __future__ import annotations

from dataclasses import dataclass

from .source_inventory import SourceContractResult, load_manifest, validate_all_sources
from .topology import derive_all_topology, reciprocal_topology_findings


@dataclass(frozen=True, slots=True)
class TopologyQualificationResult:
    spatial_reference_id: str
    reference_type: str
    topology_status: str
    reciprocal_link_count: int
    missing_direction_count: int
    finding_count: int
    detail: str


def qualify_sources() -> tuple[SourceContractResult, ...]:
    return validate_all_sources(load_manifest())


def qualify_topology() -> tuple[TopologyQualificationResult, ...]:
    rows = derive_all_topology()
    findings = reciprocal_topology_findings(rows)
    finding_by_id: dict[str, list[str]] = {}
    for finding in findings:
        finding_by_id.setdefault(finding.split(":", 1)[0], []).append(finding)
    neighbor_fields = (
        "north_id", "north_east_id", "east_id", "south_east_id",
        "south_id", "south_west_id", "west_id", "north_west_id",
    )
    out: list[TopologyQualificationResult] = []
    for row in rows:
        related = finding_by_id.get(row.spatial_reference_id, [])
        link_count = sum(bool(getattr(row, field)) for field in neighbor_fields)
        out.append(TopologyQualificationResult(
            spatial_reference_id=row.spatial_reference_id,
            reference_type="MAJOR_GRID" if row.spatial_reference_id.startswith("NG-MGRID-") else "REFERENCE_CELL",
            topology_status="PASS" if not related else "FAIL",
            reciprocal_link_count=link_count,
            missing_direction_count=8 - link_count,
            finding_count=len(related),
            detail=";".join(related),
        ))
    return tuple(out)


def bundle17a_is_qualified() -> bool:
    return all(item.contract_status == "PASS" for item in qualify_sources()) and all(
        item.topology_status == "PASS" for item in qualify_topology()
    )


__all__ = ["TopologyQualificationResult", "qualify_sources", "qualify_topology", "bundle17a_is_qualified"]
