"""Bundle 17B deterministic CSV artifact materialization."""
from __future__ import annotations

from functools import lru_cache
from dataclasses import asdict
from pathlib import Path
import csv

from ._shared import SOURCE_ROOT
from .containment import derive_containment_qualifications
from .contracts import EnvironmentEvidenceType, SovereignLandRelation
from .crs_reconciliation import derive_crs_crosswalk
from .environment_binding import derive_environment_bindings, environment_coverage_rows
from .environment_policy import environment_resolution_policy_rows, evidence_type_rows
from .precision import derive_precision_qualifications
from .source_fidelity import derive_source_fidelity_results


def artifact_paths(source_root: Path = SOURCE_ROOT) -> dict[str, Path]:
    return {
    "crs_crosswalk": source_root / "03_authority_identifiers" / "novegeo_crs_crosswalk_v001.csv",
    "precision": source_root / "06_spatial_qualification" / "novegeo_spatial_precision_qualification_v002.csv",
    "containment": source_root / "06_spatial_qualification" / "novegeo_spatial_containment_qualification_v002.csv",
    "evidence_types": source_root / "07_environment" / "novegeo_environment_evidence_type_codes_v001.csv",
    "resolution_policy": source_root / "07_environment" / "novegeo_environment_resolution_policy_v001.csv",
    "environment_bindings": source_root / "08_relationships" / "novegeo_spatial_environment_bindings_v002.csv",
    "source_fidelity": source_root / "10_evidence" / "novegeo_spatial_source_fidelity_results_v002.csv",
        "environment_coverage": source_root / "10_evidence" / "novegeo_environment_coverage_qualification_v001.csv",
    }


ARTIFACT_PATHS = artifact_paths()


def _serialize(value):
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (EnvironmentEvidenceType, SovereignLandRelation)):
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
    bindings = derive_environment_bindings()
    return {
        "crs_crosswalk": _dict_rows(derive_crs_crosswalk()),
        "precision": _dict_rows(derive_precision_qualifications()),
        "containment": _dict_rows(derive_containment_qualifications()),
        "evidence_types": tuple(evidence_type_rows()),
        "resolution_policy": tuple(environment_resolution_policy_rows()),
        "environment_bindings": _dict_rows(bindings),
        "source_fidelity": _dict_rows(derive_source_fidelity_results()),
        "environment_coverage": tuple(environment_coverage_rows(bindings)),
    }


def _write_csv(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    if not rows:
        raise ValueError(f"refusing to create empty governed Bundle 17B artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_bundle17b_artifacts(source_root: Path = SOURCE_ROOT) -> tuple[Path, ...]:
    rows = artifact_rows()
    written: list[Path] = []
    for key, path in artifact_paths(source_root).items():
        _write_csv(path, rows[key])
        written.append(path)
    return tuple(written)


def artifact_contract_findings() -> tuple[str, ...]:
    findings: list[str] = []
    expected_counts = {
        "crs_crosswalk": 27,
        "precision": 10644,
        "containment": 2411,
        "evidence_types": 5,
        "resolution_policy": 11,
        "environment_bindings": 1104,
        "source_fidelity": 5322,
        "environment_coverage": 1104,
    }
    rows = artifact_rows()
    for key, expected in expected_counts.items():
        if len(rows[key]) != expected:
            findings.append(f"{key}:EXPECTED_{expected}_GOT_{len(rows[key])}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "artifact_paths", "artifact_rows", "write_bundle17b_artifacts", "artifact_contract_findings"]
