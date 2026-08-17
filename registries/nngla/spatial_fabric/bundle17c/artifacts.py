"""Bundle 17C deterministic CSV artifact materialization."""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
import csv

from ._shared import SOURCE_ROOT, csv_rows
from .compatibility import compatibility_rule_rows
from .conflict_rules import conflict_rule_set_rows
from .contracts import CompatibilityOutcome, ConflictStatus, RelationshipType
from .occupancy import derive_occupancy_relationships
from .qualification import derive_conflict_qualification_results
from .relationship_types import relationship_type_rows


def artifact_paths(source_root: Path = SOURCE_ROOT) -> dict[str, Path]:
    return {
        "relationship_types": source_root / "02_controlled_codes" / "novegeo_spatial_relationship_type_codes_v001.csv",
        "occupancy": source_root / "08_relationships" / "novegeo_spatial_occupancy_relationships_v002.csv",
        "compatibility_rules": source_root / "02_controlled_codes" / "novegeo_feature_compatibility_rules_v001.csv",
        "conflict_rule_sets": source_root / "02_controlled_codes" / "novegeo_spatial_conflict_rule_sets_v001.csv",
        "conflict_results": source_root / "10_evidence" / "novegeo_spatial_conflict_qualification_results_v001.csv",
    }


ARTIFACT_PATHS = artifact_paths()


def _serialize(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (RelationshipType, CompatibilityOutcome, ConflictStatus)):
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
        "relationship_types": tuple(relationship_type_rows()),
        "occupancy": _dict_rows(derive_occupancy_relationships()),
        "compatibility_rules": tuple(compatibility_rule_rows()),
        "conflict_rule_sets": tuple(conflict_rule_set_rows()),
        "conflict_results": _dict_rows(derive_conflict_qualification_results()),
    }


def _write(path: Path, rows: tuple[dict[str, str], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Bundle 17C generated artifact {path.name} cannot be headerless/empty")
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
