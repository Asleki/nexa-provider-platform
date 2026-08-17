"""Bundle 17F deterministic reconciliation and qualification CSV artifacts."""
from __future__ import annotations
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
import csv

from ._shared import SPATIAL_ROOT, csv_rows
from .associations import derive_subject_spatial_association_candidates
from .canonical_alignment import derive_existing_canonical_alignment
from .contracts import AssociationStatus, CanonicalSubjectFamily
from .preconditions import derive_spatial_association_precondition_results
from .traversal import derive_geometry_traversal_qualifications


def artifact_paths(source_root: Path = SPATIAL_ROOT) -> dict[str, Path]:
    return {
        "canonical_alignment": source_root / "08_relationships" / "novegeo_existing_canonical_alignment_v002.csv",
        "association_candidates": source_root / "08_relationships" / "novegeo_subject_spatial_association_candidates_v001.csv",
        "traversal_qualification": source_root / "10_evidence" / "novegeo_geometry_traversal_qualification_v001.csv",
        "association_preconditions": source_root / "10_evidence" / "novegeo_spatial_association_precondition_results_v001.csv",
    }

ARTIFACT_PATHS = artifact_paths()


def _serialize(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (AssociationStatus, CanonicalSubjectFamily)):
        return value.value
    return str(value)


def _rows(items) -> tuple[dict[str, str], ...]:
    return tuple({k: _serialize(v) for k, v in asdict(item).items()} for item in items)


@lru_cache(maxsize=1)
def artifact_rows() -> dict[str, tuple[dict[str, str], ...]]:
    return {
        "canonical_alignment": _rows(derive_existing_canonical_alignment()),
        "association_candidates": _rows(derive_subject_spatial_association_candidates()),
        "traversal_qualification": _rows(derive_geometry_traversal_qualifications()),
        "association_preconditions": _rows(derive_spatial_association_precondition_results()),
    }


def _write(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Bundle 17F artifact cannot be empty: {path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def materialize_artifacts(source_root: Path = SPATIAL_ROOT) -> tuple[Path, ...]:
    paths = artifact_paths(source_root); rows = artifact_rows()
    for key, path in paths.items(): _write(path, rows[key])
    return tuple(paths.values())


def artifact_drift_findings(source_root: Path = SPATIAL_ROOT) -> tuple[str, ...]:
    findings = []
    for key, path in artifact_paths(source_root).items():
        if not path.is_file(): findings.append(f"MISSING:{path}")
        elif csv_rows(path) != artifact_rows()[key]: findings.append(f"DRIFT:{path}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "artifact_paths", "artifact_rows", "materialize_artifacts", "artifact_drift_findings"]
