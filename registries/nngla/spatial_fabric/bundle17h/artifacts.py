"""Bundle 17H governed CSV artifacts and drift qualification."""
from __future__ import annotations

from pathlib import Path
import csv

from ._shared import CONTROLLED_ROOT, ROADS_ADDRESSES_ROOT, csv_header, csv_rows
from .address_policy import allocation_policy_rows, address_format_rule_rows
from .lifecycle import site_lifecycle_rows, structure_reference_type_rows
from .road_segments import road_segment_rows


def artifact_paths(root: Path | None = None) -> dict[str, Path]:
    base = root or CONTROLLED_ROOT.parent
    controlled = base / "02_controlled_codes"
    roads = base / "06_roads_addresses"
    return {
        "road_segments": roads / "novegeo_road_segment_candidates_v001.csv",
        "road_frontages": roads / "novegeo_road_frontage_candidates_v001.csv",
        "allocation_policies": controlled / "novegeo_address_allocation_policy_codes_v001.csv",
        "address_series": roads / "novegeo_address_series_definitions_v001.csv",
        "address_format_rules": controlled / "novegeo_address_format_rules_v001.csv",
        "address_reservations": roads / "novegeo_address_number_reservations_v001.csv",
        "address_reference_v002": roads / "address_reference_candidates_v002.csv",
        "house_crosswalk": roads / "novegeo_house_catalogue_registry_crosswalk_v001.csv",
        "house_site_requirements": roads / "novegeo_house_design_site_requirements_v001.csv",
        "site_lifecycle": controlled / "novegeo_site_lifecycle_status_codes_v001.csv",
        "structure_types": controlled / "novegeo_structure_reference_type_codes_v001.csv",
        "site_candidates": roads / "novegeo_addressable_site_candidates_v001.csv",
        "structure_site_references": roads / "novegeo_structure_site_references_v001.csv",
        "site_address_assignments": roads / "novegeo_site_address_assignment_candidates_v001.csv",
    }


ARTIFACT_PATHS = artifact_paths()
ARTIFACT_HEADERS = {
    "road_segments": ("road_segment_id","road_id","source_road_candidate_id","segment_sequence","segment_role","geometry_id","start_measure_m","end_measure_m","geometry_status","addressing_scope_eligible","runtime_effect_scope","source_reference"),
    "road_frontages": ("frontage_id","site_id","road_id","road_segment_id","frontage_role","access_status","qualification_status","source_reference"),
    "allocation_policies": tuple(allocation_policy_rows()[0]),
    "address_series": ("series_id","road_id","road_segment_id","policy_code","scope_type","scope_reference","start_number","sequence_step","number_format_rule_code","side_rule","allow_suffix","status","source_reference"),
    "address_format_rules": tuple(address_format_rule_rows()[0]),
    "address_reservations": ("reservation_id","series_id","site_id","reserved_address_id","display_address_number","normalized_number_key","idempotency_key","reservation_status","canonical_address_created","authority_runtime_mode","source_reference"),
    "address_reference_v002": ("address_candidate_id","road_id","road_segment_id","address_series_id","site_id","premise_sequence","unit_designator","display_address_number","place_id","administrative_area_id","parcel_id","allocation_status","address_status","reserved_at","assigned_at","retired_at","source_reference","runtime_effect_scope"),
    "house_crosswalk": ("citizen_house_design_id","citizen_house_design_code","legacy_place_registry_reference","governed_place_dataset_id","current_place_source","source_catalogue","source_catalogue_sha256","crosswalk_status"),
    "house_site_requirements": ("citizen_house_design_id","citizen_house_design_code","primary_compatible_terrain_zone","compatible_terrain_zones","minimum_plot_area_sqm","suitable_ground_conditions","unsuitable_ground_conditions","maximum_site_slope_percent","minimum_floor_clearance_mm","flood_resilience_level","wind_resistance_level","drainage_requirement","site_inspection_requirement","physical_property_id_issue_stage","source_catalogue_sha256"),
    "site_lifecycle": tuple(site_lifecycle_rows()[0]),
    "structure_types": tuple(structure_reference_type_rows()[0]),
    "site_candidates": ("site_id","place_id","administrative_area_id","parcel_id","geometry_id","road_id","road_segment_id","lifecycle_stage","runtime_mode","source_reference"),
    "structure_site_references": ("structure_site_reference_id","site_id","structure_reference_type_code","external_registry_code","external_structure_reference","effective_from","effective_to","reference_status","source_reference"),
    "site_address_assignments": ("assignment_candidate_id","site_id","address_reservation_id","address_id","assignment_status","runtime_mode","source_reference"),
}


def _stable_rows_from_existing() -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "road_segments": road_segment_rows(),
        "road_frontages": (),
        "allocation_policies": allocation_policy_rows(),
        "address_series": (),
        "address_format_rules": address_format_rule_rows(),
        "address_reservations": (),
        "address_reference_v002": (),
        "site_lifecycle": site_lifecycle_rows(),
        "structure_types": structure_reference_type_rows(),
        "site_candidates": (),
        "structure_site_references": (),
        "site_address_assignments": (),
    }


def _write(path: Path, header: tuple[str, ...], rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader(); writer.writerows(rows)


def materialize_static_artifacts(base: Path | None = None) -> tuple[Path, ...]:
    paths = artifact_paths(base); rows = _stable_rows_from_existing()
    for key, values in rows.items():
        _write(paths[key], ARTIFACT_HEADERS[key], values)
    return tuple(paths[key] for key in rows)


def artifact_drift_findings(base: Path | None = None) -> tuple[str, ...]:
    paths = artifact_paths(base); expected = _stable_rows_from_existing(); findings = []
    for key, values in expected.items():
        path = paths[key]
        if not path.is_file(): findings.append(f"MISSING:{path}"); continue
        if csv_header(path) != ARTIFACT_HEADERS[key]: findings.append(f"HEADER_DRIFT:{path}")
        if csv_rows(path) != values: findings.append(f"ROW_DRIFT:{path}")
    for key in ("house_crosswalk", "house_site_requirements"):
        path = paths[key]
        if not path.is_file(): findings.append(f"MISSING:{path}"); continue
        if csv_header(path) != ARTIFACT_HEADERS[key]: findings.append(f"HEADER_DRIFT:{path}")
        rows = csv_rows(path)
        if len(rows) != 120: findings.append(f"HOUSE_ROW_COUNT_DRIFT:{key}:{len(rows)}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "ARTIFACT_HEADERS", "artifact_paths", "materialize_static_artifacts", "artifact_drift_findings"]
