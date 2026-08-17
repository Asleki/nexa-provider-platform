"""Bundle 17I governed title/state-land CSV artifacts and drift qualification."""
from __future__ import annotations

from pathlib import Path
import csv

from ._shared import CADASTRE_ROOT, csv_header, csv_rows
from .title_series import title_number_series_rows
from .lifecycle import title_lifecycle_rows


def artifact_paths(root: Path = CADASTRE_ROOT) -> dict[str, Path]:
    controlled = root / "02_controlled_codes"
    land = root / "07_land"
    return {
        "title_series": controlled / "novegeo_title_number_series_definitions_v001.csv",
        "title_reservations": land / "novegeo_title_reference_reservations_v001.csv",
        "title_lifecycle": controlled / "novegeo_title_lifecycle_status_codes_v001.csv",
        "title_issuance_candidates": land / "novegeo_title_issuance_candidates_v001.csv",
        "state_land_candidates": land / "novegeo_state_land_candidate_records_v001.csv",
        "title_bootstrap_v002": land / "title_bootstrap_v002.csv",
        "state_land_bootstrap_v002": land / "state_land_bootstrap_v002.csv",
    }


ARTIFACT_PATHS = artifact_paths()
ARTIFACT_HEADERS = {
    "title_series": tuple(title_number_series_rows()[0]),
    "title_reservations": ("reservation_id","series_id","reserved_title_id","parcel_id","holder_reference","idempotency_key","reservation_status","legal_title_exists","authority_runtime_mode","source_reference"),
    "title_lifecycle": tuple(title_lifecycle_rows()[0]),
    "title_issuance_candidates": ("issuance_candidate_id","reservation_id","title_id","parcel_id","title_type_code","tenure_type_code","holder_reference","issuance_status","prior_title_id","runtime_mode","source_reference"),
    "state_land_candidates": ("state_land_candidate_id","parcel_id","state_land_category_code","administrative_area_id","candidate_status","legal_state_land_exists","runtime_mode","source_reference"),
    "title_bootstrap_v002": ("title_id","parcel_id","title_type_code","tenure_type_code","holder_reference","title_status","effective_from","effective_to","source_reference","runtime_effect_scope"),
    "state_land_bootstrap_v002": ("state_land_record_id","parcel_id","state_land_category_code","administrative_area_id","status","effective_from","effective_to","source_reference","runtime_effect_scope"),
}


def artifact_rows() -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "title_series": title_number_series_rows(),
        "title_reservations": (),
        "title_lifecycle": title_lifecycle_rows(),
        "title_issuance_candidates": (),
        "state_land_candidates": (),
        "title_bootstrap_v002": (),
        "state_land_bootstrap_v002": (),
    }


def _write(path: Path, header: tuple[str, ...], rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header); writer.writeheader(); writer.writerows(rows)


def materialize_artifacts(root: Path = CADASTRE_ROOT) -> tuple[Path, ...]:
    paths=artifact_paths(root); rows=artifact_rows()
    for key,path in paths.items(): _write(path, ARTIFACT_HEADERS[key], rows[key])
    return tuple(paths.values())


def artifact_drift_findings(root: Path = CADASTRE_ROOT) -> tuple[str, ...]:
    findings=[]; paths=artifact_paths(root); rows=artifact_rows()
    for key,path in paths.items():
        if not path.is_file(): findings.append(f"MISSING:{path}"); continue
        if csv_header(path) != ARTIFACT_HEADERS[key]: findings.append(f"HEADER_DRIFT:{path}")
        if csv_rows(path) != rows[key]: findings.append(f"ROW_DRIFT:{path}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "ARTIFACT_HEADERS", "artifact_paths", "artifact_rows", "materialize_artifacts", "artifact_drift_findings"]
