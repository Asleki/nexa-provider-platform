"""Bundle 17G governed policy, lifecycle and empty operational-register artifacts."""
from __future__ import annotations
from pathlib import Path
import csv

from ._shared import CADASTRE_ROOT, csv_header, csv_rows
from .cadastral_series import cadastral_series_policy_rows
from .lifecycle import parcel_lifecycle_rows


def artifact_paths(source_root: Path = CADASTRE_ROOT) -> dict[str, Path]:
    return {
        "cadastral_series_definitions": source_root / "02_controlled_codes" / "novegeo_cadastral_series_definitions_v001.csv",
        "parcel_lifecycle_status_codes": source_root / "02_controlled_codes" / "novegeo_parcel_lifecycle_status_codes_v001.csv",
        "parcel_candidates": source_root / "07_land" / "novegeo_parcel_candidate_records_v001.csv",
        "parcel_reservations": source_root / "07_land" / "novegeo_parcel_reference_reservations_v001.csv",
        "parcel_geometry_candidates": source_root / "07_land" / "novegeo_parcel_geometry_candidates_v001.csv",
        "parcel_lineage_candidates": source_root / "07_land" / "novegeo_parcel_lineage_candidates_v001.csv",
        "parcel_bootstrap_v002": source_root / "07_land" / "parcel_bootstrap_v002.csv",
    }

ARTIFACT_PATHS = artifact_paths()

ARTIFACT_HEADERS = {
    "cadastral_series_definitions": tuple(cadastral_series_policy_rows()[0]),
    "parcel_lifecycle_status_codes": tuple(parcel_lifecycle_rows()[0]),
    "parcel_candidates": (
        "parcel_candidate_id", "physical_ground_reference", "proposed_land_use_code", "proposed_geometry_id",
        "survey_status", "lifecycle_stage", "runtime_mode", "runtime_effect_scope", "source_reference",
    ),
    "parcel_reservations": (
        "reservation_id", "parcel_candidate_id", "parcel_id", "cadastral_zone", "cadastral_series", "parcel_sequence",
        "reservation_status", "legal_effect", "canonical_parcel_registered", "authority_runtime_mode", "source_reference",
    ),
    "parcel_geometry_candidates": (
        "parcel_geometry_candidate_id", "parcel_candidate_id", "geometry_id", "geometry_type_code", "crs_code",
        "ring_closed", "geometry_valid", "sovereign_land_relation", "overlap_status", "survey_id", "geometry_status", "source_reference",
    ),
    "parcel_lineage_candidates": (
        "lineage_candidate_id", "action", "predecessor_parcel_ids", "successor_parcel_ids", "effective_on", "source_reference",
    ),
    "parcel_bootstrap_v002": (
        "parcel_id", "parent_parcel_id", "cadastral_series", "parcel_sequence", "parcel_status", "geometry_reference",
        "land_use_code", "survey_status", "created_effective_at", "retired_effective_at", "source_reference", "runtime_effect_scope",
    ),
}


def artifact_rows() -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "cadastral_series_definitions": cadastral_series_policy_rows(),
        "parcel_lifecycle_status_codes": parcel_lifecycle_rows(),
        "parcel_candidates": (),
        "parcel_reservations": (),
        "parcel_geometry_candidates": (),
        "parcel_lineage_candidates": (),
        "parcel_bootstrap_v002": (),
    }


def _write(path: Path, header: tuple[str, ...], rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader(); writer.writerows(rows)


def materialize_artifacts(source_root: Path = CADASTRE_ROOT) -> tuple[Path, ...]:
    paths = artifact_paths(source_root); rows = artifact_rows()
    for key, path in paths.items(): _write(path, ARTIFACT_HEADERS[key], rows[key])
    return tuple(paths.values())


def artifact_drift_findings(source_root: Path = CADASTRE_ROOT) -> tuple[str, ...]:
    findings = []
    expected_rows = artifact_rows()
    for key, path in artifact_paths(source_root).items():
        if not path.is_file():
            findings.append(f"MISSING:{path}"); continue
        if csv_header(path) != ARTIFACT_HEADERS[key]: findings.append(f"HEADER_DRIFT:{path}")
        if csv_rows(path) != expected_rows[key]: findings.append(f"ROW_DRIFT:{path}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "ARTIFACT_HEADERS", "artifact_paths", "artifact_rows", "materialize_artifacts", "artifact_drift_findings"]
