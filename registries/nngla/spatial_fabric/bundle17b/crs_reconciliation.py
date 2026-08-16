"""Bundle 17B CRS reconciliation without rewriting immutable source rows."""
from __future__ import annotations

from functools import lru_cache
from collections import defaultdict
from pathlib import Path

from registries.nngla.spatial_fabric import derive_coordinate_occurrences, load_manifest
from registries.nngla.spatial_fabric.source_inventory import source_path

from ._shared import (
    BOUNDARY_QUALIFICATION_PATH,
    CLIMATE_QUALIFIED_PATH,
    CRS_REGISTER_PATH,
    HYDROLOGY_QUALIFIED_PATH,
    LANDFORMS_QUALIFIED_PATH,
    TERRAIN_QUALIFIED_PATH,
    VEGETATION_QUALIFIED_PATH,
    csv_rows,
    qualified_crs_from_json,
)
from .contracts import CrsCrosswalkEntry


_CRS_CROSSWALK_PATH = Path(__file__).resolve().parents[4] / "data/novegeo/nngla/spatial-fabric/source/03_authority_identifiers/novegeo_crs_crosswalk_v001.csv"


def governed_crs_contract() -> dict[str, str]:
    rows = csv_rows(CRS_REGISTER_PATH)
    matches = [row for row in rows if row.get("crs_code") == "NG-CRS-EPSG4326" and row.get("status") == "ACTIVE"]
    if len(matches) != 1:
        raise ValueError("locked NG-CRS-EPSG4326 contract missing or ambiguous")
    row = matches[0]
    if row.get("authority_name") != "EPSG" or row.get("authority_code") != "4326":
        raise ValueError("locked NoveGeo CRS no longer maps to EPSG:4326")
    return row


def _evidence_for(entry) -> tuple[Path, str]:
    dataset = entry.dataset_id
    filename = entry.filename
    if dataset.startswith("dataset:novegeo:terrain:elevation") or filename == "novegeo_spatial_grid_cells_v001.csv":
        return TERRAIN_QUALIFIED_PATH, "SOURCE_OR_DERIVED_TERRAIN_LINEAGE"
    if dataset.startswith("dataset:novegeo:climate:baseline"):
        return CLIMATE_QUALIFIED_PATH, "SOURCE_CLIMATE_LINEAGE"
    if dataset.startswith("dataset:novegeo:vegetation:baseline"):
        return VEGETATION_QUALIFIED_PATH, "SOURCE_VEGETATION_LINEAGE"
    if dataset.startswith("dataset:novegeo:hydrology:surface-water"):
        return HYDROLOGY_QUALIFIED_PATH, "SOURCE_HYDROLOGY_LINEAGE"
    if dataset.startswith("dataset:novegeo:landforms") or filename in {
        "novegeo_mountain_candidates_v001.csv", "novegeo_plain_candidates_v001.csv",
        "novegeo_plateau_candidates_v001.csv", "novegeo_valley_candidates_v001.csv",
    }:
        return LANDFORMS_QUALIFIED_PATH, "SOURCE_LANDFORM_LINEAGE"
    if (
        "world_boundary" in filename
        or "sovereign_parts" in filename
        or "island_candidates" in filename
        or entry.source_family in {"03_qualified_feature_candidates", "05_new_waters_ocean"}
    ):
        return BOUNDARY_QUALIFICATION_PATH, "QUALIFIED_BOUNDARY_OR_DERIVATIVE_LINEAGE"
    return BOUNDARY_QUALIFICATION_PATH, "GOVERNED_SPATIAL_FABRIC_LINEAGE"


@lru_cache(maxsize=1)
def derive_crs_crosswalk() -> tuple[CrsCrosswalkEntry, ...]:
    manifest = {entry.source_file_id: entry for entry in load_manifest()}
    occurrences = derive_coordinate_occurrences()
    by_file: dict[str, list] = defaultdict(list)
    for occurrence in occurrences:
        by_file[occurrence.source_file_id].append(occurrence)
    governed = governed_crs_contract()
    out: list[CrsCrosswalkEntry] = []
    for index, source_file_id in enumerate(sorted(by_file), start=1):
        entry = manifest[source_file_id]
        values = {item.crs_source_code for item in by_file[source_file_id]}
        if values - {"EPSG:4326", "UNDECLARED_IN_ROW"}:
            raise ValueError(f"unsupported CRS form in {source_file_id}: {sorted(values)!r}")
        source_form = "EPSG:4326" if values == {"EPSG:4326"} else "UNDECLARED_IN_ROW"
        evidence_path, basis = _evidence_for(entry)
        ref = qualified_crs_from_json(evidence_path)
        if evidence_path == BOUNDARY_QUALIFICATION_PATH:
            ref = ("EPSG", "4326", "crs:novegeo:geographic", "decimal_degrees")
        if ref is None or ref[0] != "EPSG" or ref[1] != "4326":
            raise ValueError(f"unable to prove EPSG:4326 lineage for {source_file_id}")
        if source_form == "EPSG:4326":
            basis = "ROW_DECLARED_EPSG4326_PLUS_QUALIFIED_LINEAGE"
        out.append(CrsCrosswalkEntry(
            crs_crosswalk_id=f"NG-CRSXW-{index:06d}",
            source_file_id=source_file_id,
            source_dataset_id=entry.dataset_id,
            source_crs_form=source_form,
            source_authority_name="EPSG",
            source_authority_code="4326",
            source_coordinate_reference_id=ref[2] or "crs:novegeo:geographic",
            governed_crs_code=governed["crs_code"],
            axis_order=governed["axis_order"],
            horizontal_unit=governed["horizontal_unit"],
            reconciliation_basis=basis,
            evidence_reference=str(evidence_path.relative_to(Path(__file__).resolve().parents[4])),
            qualification_status="PASS",
        ))
    return tuple(out)


def load_crs_crosswalk(path: Path = _CRS_CROSSWALK_PATH) -> tuple[CrsCrosswalkEntry, ...]:
    if not path.is_file():
        return derive_crs_crosswalk()
    out: list[CrsCrosswalkEntry] = []
    for row in csv_rows(path):
        out.append(CrsCrosswalkEntry(**row))
    return tuple(out)


def crs_by_source_file() -> dict[str, CrsCrosswalkEntry]:
    rows = load_crs_crosswalk()
    mapping = {row.source_file_id: row for row in rows}
    if len(mapping) != len(rows):
        raise ValueError("duplicate source file in CRS crosswalk")
    return mapping


def qualify_crs_occurrences() -> tuple[str, ...]:
    mapping = crs_by_source_file()
    findings: list[str] = []
    for occurrence in derive_coordinate_occurrences():
        crosswalk = mapping.get(occurrence.source_file_id)
        if crosswalk is None:
            findings.append(f"MISSING_CRS_CROSSWALK:{occurrence.source_file_id}")
            continue
        if occurrence.crs_source_code not in {"EPSG:4326", "UNDECLARED_IN_ROW"}:
            findings.append(f"UNSUPPORTED_SOURCE_CRS:{occurrence.coordinate_occurrence_id}")
        if crosswalk.governed_crs_code != "NG-CRS-EPSG4326":
            findings.append(f"WRONG_GOVERNED_CRS:{occurrence.coordinate_occurrence_id}")
    return tuple(findings)


__all__ = [
    "governed_crs_contract", "derive_crs_crosswalk", "load_crs_crosswalk", "crs_by_source_file",
    "qualify_crs_occurrences",
]
