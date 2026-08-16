"""Internal Bundle 17B deterministic data-access helpers."""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import csv
import json

from registries.nngla.spatial_fabric.source_inventory import ROOT, SOURCE_ROOT


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def json_value(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def decimal_places(text: str) -> int:
    raw = str(text).strip().lower()
    if "e" in raw:
        value = Decimal(raw)
        exponent = value.as_tuple().exponent
        return max(0, -exponent)
    return len(raw.partition(".")[2]) if "." in raw else 0


def qualified_crs_from_json(path: Path) -> tuple[str, str, str, str] | None:
    """Return authority, authority code, coordinate reference id, unit when declared."""
    value = json_value(path)
    if isinstance(value, dict):
        ref = value.get("coordinateReference")
        if isinstance(ref, dict):
            return (
                str(ref.get("authorityName", "")),
                str(ref.get("authorityCode", "")),
                str(ref.get("coordinateReferenceId", "")),
                str(ref.get("unit", "")),
            )
        props = value.get("properties")
        if isinstance(props, dict) and props.get("coordinateReferenceId"):
            return ("EPSG", "4326", str(props["coordinateReferenceId"]), "decimal_degrees")
    return None


def recursively_collect_coordinate_pairs(value) -> set[tuple[Decimal, Decimal]]:
    """Collect explicit longitude/latitude objects and GeoJSON coordinate pairs."""
    pairs: set[tuple[Decimal, Decimal]] = set()

    def walk(node, key: str = "") -> None:
        if isinstance(node, dict):
            if "longitude" in node and "latitude" in node:
                try:
                    pairs.add((Decimal(str(node["longitude"])), Decimal(str(node["latitude"]))))
                except Exception:
                    pass
            for k, v in node.items():
                walk(v, str(k))
            return
        if isinstance(node, list):
            if key == "coordinates" and len(node) >= 2 and all(isinstance(x, (int, float, str)) for x in node[:2]):
                try:
                    pairs.add((Decimal(str(node[0])), Decimal(str(node[1]))))
                    return
                except Exception:
                    pass
            for item in node:
                walk(item, key)

    walk(value)
    return pairs


BOUNDARY_CANDIDATE_PATH = ROOT / "data/novegeo/geography/world-boundary/candidate/novegeo_world_boundary_v002.geojson"
BOUNDARY_QUALIFICATION_PATH = ROOT / "data/novegeo/geography/world-boundary/qualification/novegeo_world_boundary_v002_qualification.json"
TERRAIN_QUALIFIED_PATH = ROOT / "data/novegeo/geography/terrain/qualified/novegeo_terrain_v001.json"
CLIMATE_QUALIFIED_PATH = ROOT / "data/novegeo/geography/climate/qualified/novegeo_climate_v001.json"
VEGETATION_QUALIFIED_PATH = ROOT / "data/novegeo/geography/vegetation/qualified/novegeo_vegetation_v001.json"
HYDROLOGY_QUALIFIED_PATH = ROOT / "data/novegeo/geography/hydrology/qualified/novegeo_hydrology_v001.json"
LANDFORMS_QUALIFIED_PATH = ROOT / "data/novegeo/geography/landforms/qualified/novegeo_landforms_v001.geojson"
CRS_REGISTER_PATH = ROOT / "data/novegeo/nngla/geometry-roads-addresses/source/02_controlled_codes/coordinate_reference_systems.csv"


__all__ = [
    "ROOT", "SOURCE_ROOT", "csv_rows", "file_sha256", "json_value", "decimal_text", "decimal_places",
    "qualified_crs_from_json", "recursively_collect_coordinate_pairs",
    "BOUNDARY_CANDIDATE_PATH", "BOUNDARY_QUALIFICATION_PATH", "TERRAIN_QUALIFIED_PATH", "CLIMATE_QUALIFIED_PATH",
    "VEGETATION_QUALIFIED_PATH", "HYDROLOGY_QUALIFIED_PATH", "LANDFORMS_QUALIFIED_PATH", "CRS_REGISTER_PATH",
]
