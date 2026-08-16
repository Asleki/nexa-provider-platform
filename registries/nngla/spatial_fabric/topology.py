"""Bundle 17A deterministic topology derived from actual spatial coordinates."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import csv

from .contracts import SpatialNeighborTopology, parse_decimal
from .source_inventory import SOURCE_ROOT

_GRID_PATH = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_major_grid_boxes_v001.csv"
_CELL_PATH = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_spatial_grid_cells_v001.csv"

_DIRECTIONS = (
    ("north_id", Decimal("0"), Decimal("1")),
    ("north_east_id", Decimal("1"), Decimal("1")),
    ("east_id", Decimal("1"), Decimal("0")),
    ("south_east_id", Decimal("1"), Decimal("-1")),
    ("south_id", Decimal("0"), Decimal("-1")),
    ("south_west_id", Decimal("-1"), Decimal("-1")),
    ("west_id", Decimal("-1"), Decimal("0")),
    ("north_west_id", Decimal("-1"), Decimal("1")),
)
_OPPOSITE = {
    "north_id": "south_id", "north_east_id": "south_west_id", "east_id": "west_id",
    "south_east_id": "north_west_id", "south_id": "north_id", "south_west_id": "north_east_id",
    "west_id": "east_id", "north_west_id": "south_east_id",
}


def _rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def derive_major_grid_topology() -> tuple[SpatialNeighborTopology, ...]:
    rows = _rows(_GRID_PATH)
    by_position = {(int(r["grid_row_from_north"]), int(r["grid_column_from_west"])): r for r in rows}
    out: list[SpatialNeighborTopology] = []
    offsets = {
        "north_id": (-1, 0), "north_east_id": (-1, 1), "east_id": (0, 1),
        "south_east_id": (1, 1), "south_id": (1, 0), "south_west_id": (1, -1),
        "west_id": (0, -1), "north_west_id": (-1, -1),
    }
    for row in sorted(rows, key=lambda r: (int(r["grid_row_from_north"]), int(r["grid_column_from_west"]))):
        pos = (int(row["grid_row_from_north"]), int(row["grid_column_from_west"]))
        neighbors = {}
        for field, delta in offsets.items():
            candidate = by_position.get((pos[0] + delta[0], pos[1] + delta[1]))
            neighbors[field] = candidate["major_grid_id"] if candidate else ""
        out.append(SpatialNeighborTopology(
            spatial_reference_id=row["major_grid_id"],
            **neighbors,
            topology_basis="MAJOR_GRID_ROW_COLUMN_WITH_BOUNDING_BOX_ORDER",
            topology_status="VALID",
        ))
    return tuple(out)


def derive_reference_cell_topology() -> tuple[SpatialNeighborTopology, ...]:
    rows = _rows(_CELL_PATH)
    by_coordinate = {
        (parse_decimal(r["centre_longitude"]), parse_decimal(r["centre_latitude"])): r
        for r in rows
    }
    if len(by_coordinate) != len(rows):
        raise ValueError("reference-cell centers are not unique")
    out: list[SpatialNeighborTopology] = []
    for row in sorted(rows, key=lambda r: int(r["spatial_cell_id"].rsplit("-", 1)[1])):
        lon = parse_decimal(row["centre_longitude"])
        lat = parse_decimal(row["centre_latitude"])
        spacing = parse_decimal(row["nominal_spacing_degrees"])
        neighbors: dict[str, str] = {}
        for field, dx, dy in _DIRECTIONS:
            candidate = by_coordinate.get((lon + dx * spacing, lat + dy * spacing))
            neighbors[field] = candidate["spatial_cell_id"] if candidate else ""
        out.append(SpatialNeighborTopology(
            spatial_reference_id=row["spatial_cell_id"],
            **neighbors,
            topology_basis="EXACT_DECIMAL_CENTER_COORDINATE_PLUS_DECLARED_SPACING",
            topology_status="VALID",
        ))
    return tuple(out)


def derive_all_topology() -> tuple[SpatialNeighborTopology, ...]:
    return derive_major_grid_topology() + derive_reference_cell_topology()


def reciprocal_topology_findings(rows: tuple[SpatialNeighborTopology, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_all_topology()
    by_id = {row.spatial_reference_id: row for row in current}
    findings: list[str] = []
    for row in current:
        for field, opposite in _OPPOSITE.items():
            neighbor_id = getattr(row, field)
            if not neighbor_id:
                continue
            neighbor = by_id.get(neighbor_id)
            if neighbor is None:
                findings.append(f"{row.spatial_reference_id}:{field}:UNKNOWN_NEIGHBOR:{neighbor_id}")
                continue
            if getattr(neighbor, opposite) != row.spatial_reference_id:
                findings.append(f"{row.spatial_reference_id}:{field}:NON_RECIPROCAL:{neighbor_id}")
    return tuple(findings)


__all__ = [
    "derive_major_grid_topology",
    "derive_reference_cell_topology",
    "derive_all_topology",
    "reciprocal_topology_findings",
]
