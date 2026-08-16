"""Deterministic Bundle 17A CSV artifact generation.

Generated files are evidence/candidate outputs only.  This module performs no
network or PostgreSQL access.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import csv
import json
import re

from .contracts import canonical_decimal_text
from .coordinate_occurrences import (
    derive_coordinate_candidates,
    derive_coordinate_occurrences,
    occurrence_crosswalk_rows,
)
from .qualification import qualify_sources, qualify_topology
from .source_inventory import ROOT, SOURCE_ROOT, load_manifest, source_row_count, source_sha256
from .topology import derive_all_topology


MANIFEST_FIELDS = (
    "source_file_id", "filename", "source_path", "source_family", "dataset_id", "dataset_version",
    "source_sha256", "record_count", "classification", "evidence_role", "contains_coordinates",
    "contains_geometry", "contains_names", "already_canonical_domain", "allowed_migration_action", "status",
)


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_derived_artifacts(root: Path = SOURCE_ROOT) -> dict[str, Path]:
    manifest = load_manifest(root / "00_manifest" / "novegeo_spatial_source_manifest_v002.csv")
    occurrences = derive_coordinate_occurrences(manifest)
    candidates = derive_coordinate_candidates(occurrences)
    crosswalk = occurrence_crosswalk_rows(occurrences)
    topology = derive_all_topology()
    source_results = qualify_sources()
    topology_results = qualify_topology()

    outputs: dict[str, Path] = {}
    p = root / "05_spatial_candidates" / "novegeo_coordinate_occurrences_v002.csv"
    _write_csv(p, (
        "coordinate_occurrence_id", "source_file_id", "source_record_id", "parent_object_type", "parent_object_id",
        "geometry_role", "ring_id", "vertex_sequence", "source_longitude_text", "source_latitude_text",
        "source_longitude_numeric", "source_latitude_numeric", "crs_source_code", "source_version",
    ), [{
        **asdict(o),
        "source_longitude_numeric": canonical_decimal_text(o.source_longitude_numeric),
        "source_latitude_numeric": canonical_decimal_text(o.source_latitude_numeric),
    } for o in occurrences])
    outputs[p.name] = p

    p = root / "05_spatial_candidates" / "novegeo_coordinate_candidates_v002.csv"
    _write_csv(p, (
        "coordinate_candidate_id", "canonical_longitude", "canonical_latitude", "governed_crs_code",
        "occurrence_count", "land_marine_classification", "canonicalization_status",
    ), [{
        **asdict(c),
        "canonical_longitude": canonical_decimal_text(c.canonical_longitude),
        "canonical_latitude": canonical_decimal_text(c.canonical_latitude),
    } for c in candidates])
    outputs[p.name] = p

    p = root / "08_relationships" / "novegeo_coordinate_occurrence_crosswalk_v002.csv"
    _write_csv(p, ("coordinate_occurrence_id", "coordinate_candidate_id", "crosswalk_basis", "crosswalk_status"), list(crosswalk))
    outputs[p.name] = p

    p = root / "08_relationships" / "novegeo_spatial_neighbor_topology_v002.csv"
    _write_csv(p, (
        "spatial_reference_id", "north_id", "north_east_id", "east_id", "south_east_id", "south_id",
        "south_west_id", "west_id", "north_west_id", "topology_basis", "topology_status",
    ), [asdict(row) for row in topology])
    outputs[p.name] = p

    p = root / "10_evidence" / "novegeo_spatial_source_contract_results_v001.csv"
    _write_csv(p, (
        "source_file_id", "source_path", "expected_sha256", "actual_sha256", "expected_row_count", "actual_row_count",
        "header_present", "namespace_contract_status", "contract_status", "findings",
    ), [{**asdict(row), "header_present": str(row.header_present).lower()} for row in source_results])
    outputs[p.name] = p

    p = root / "10_evidence" / "novegeo_spatial_topology_qualification_results_v001.csv"
    _write_csv(p, (
        "spatial_reference_id", "reference_type", "topology_status", "reciprocal_link_count",
        "missing_direction_count", "finding_count", "detail",
    ), [asdict(row) for row in topology_results])
    outputs[p.name] = p
    return outputs


def artifact_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


__all__ = ["write_derived_artifacts", "artifact_sha256"]
