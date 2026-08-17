"""Bundle 17D deterministic controlled-code and qualification artifacts."""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
import csv

from ._shared import SOURCE_ROOT, csv_rows
from .contracts import MarineSubjectType
from .feature_type_extensions import feature_type_extension_rows
from .marine_qualification import derive_marine_spatial_qualification_results
from .marine_route_types import marine_route_type_rows


def artifact_paths(source_root: Path = SOURCE_ROOT) -> dict[str, Path]:
    return {
        "feature_type_extensions": source_root / "02_controlled_codes" / "novegeo_feature_type_code_extensions_v001.csv",
        "marine_route_types": source_root / "02_controlled_codes" / "novegeo_marine_route_type_codes_v001.csv",
        "marine_qualification": source_root / "10_evidence" / "novegeo_marine_spatial_qualification_results_v001.csv",
    }


ARTIFACT_PATHS = artifact_paths()


def _serialize(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, MarineSubjectType):
        return value.value
    return str(value)


def _dict_rows(values) -> tuple[dict[str, str], ...]:
    out = []
    for item in values:
        raw = asdict(item) if not isinstance(item, dict) else item
        out.append({key: _serialize(value) for key, value in raw.items()})
    return tuple(out)


@lru_cache(maxsize=1)
def artifact_rows() -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "feature_type_extensions": tuple(feature_type_extension_rows()),
        "marine_route_types": tuple(marine_route_type_rows()),
        "marine_qualification": _dict_rows(derive_marine_spatial_qualification_results()),
    }


def _write(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Bundle 17D generated artifact {path.name} cannot be empty")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def materialize_artifacts(source_root: Path = SOURCE_ROOT) -> tuple[Path, ...]:
    paths = artifact_paths(source_root)
    rows = artifact_rows()
    for key, path in paths.items():
        _write(path, rows[key])
    return tuple(paths.values())


def artifact_drift_findings(source_root: Path = SOURCE_ROOT) -> tuple[str, ...]:
    findings = []
    paths = artifact_paths(source_root)
    expected = artifact_rows()
    for key, path in paths.items():
        if not path.is_file():
            findings.append(f"MISSING:{path}")
            continue
        if csv_rows(path) != expected[key]:
            findings.append(f"DRIFT:{path}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "artifact_paths", "artifact_rows", "materialize_artifacts", "artifact_drift_findings"]
