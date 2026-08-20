"""Protect candidate/canonical boundaries that must survive real migration."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .contracts import CandidateStateReport

ROAD_PATH = Path("data/novegeo/nngla/geometry-roads-addresses/source/06_roads_addresses/road_reference_candidates.csv")
ALIGNMENT_PATH = Path("data/novegeo/nngla/spatial-fabric/source/08_relationships/novegeo_existing_canonical_alignment_v002.csv")
FEATURE_RESULTS_PATH = Path("data/novegeo/nngla/spatial-fabric/source/10_evidence/novegeo_feature_recognition_results_v001.csv")


def _rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def assess_candidate_state(root: Path) -> CandidateStateReport:
    roads = _rows(root / ROAD_PATH)
    alignment = _rows(root / ALIGNMENT_PATH)
    feature_results = _rows(root / FEATURE_RESULTS_PATH)
    findings: list[str] = []

    road_ids = [row["road_candidate_id"] for row in roads]
    locked_road_rows = [row for row in alignment if row["object_family"] == "ROAD"]
    locked_road_ids = [row["candidate_id"] for row in locked_road_rows]

    if len(road_ids) != len(set(road_ids)):
        findings.append("ROAD_CANDIDATE_IDS_NOT_UNIQUE")
    if len(locked_road_ids) != len(set(locked_road_ids)):
        findings.append("LOCKED_ROAD_ALIGNMENT_NOT_UNIQUE")
    if set(locked_road_ids) - set(road_ids):
        findings.append("LOCKED_ROAD_ALIGNMENT_NOT_IN_SOURCE")

    expected_locked = {f"NG-RD-CAND-{i:06d}" for i in range(1, 351)}
    if set(locked_road_ids) != expected_locked:
        findings.append("LOCKED_ROAD_BASELINE_IS_NOT_FIRST_350")

    dispositions = Counter(row["disposition"] for row in feature_results)
    statuses = Counter(row["result_status"] for row in feature_results)
    if dispositions.get("REUSE_CANONICAL", 0) != 21:
        findings.append("FEATURE_REUSE_COUNT_CHANGED")
    if dispositions.get("RECOGNIZE_NEW", 0) != 5:
        findings.append("FEATURE_PENDING_RECOGNITION_COUNT_CHANGED")
    if dispositions.get("DEFER", 0) != 11:
        findings.append("FEATURE_DEFERRED_COUNT_CHANGED")
    if statuses.get("EXISTING_CANONICAL_REUSED", 0) != 21:
        findings.append("FEATURE_EXISTING_STATUS_CHANGED")
    if statuses.get("QUALIFIED_PENDING_PRODUCTION_RECOGNITION", 0) != 5:
        findings.append("FEATURE_PENDING_STATUS_CHANGED")
    if statuses.get("DEFERRED_PENDING_EVIDENCE", 0) != 11:
        findings.append("FEATURE_DEFERRED_STATUS_CHANGED")

    return CandidateStateReport(
        road_candidate_count=len(roads),
        locked_road_count=len(locked_road_rows),
        candidate_only_road_count=len(roads) - len(locked_road_rows),
        feature_candidate_count=len(feature_results),
        feature_reuse_count=dispositions.get("REUSE_CANONICAL", 0),
        feature_pending_recognition_count=dispositions.get("RECOGNIZE_NEW", 0),
        feature_deferred_count=dispositions.get("DEFER", 0),
        findings=tuple(findings),
    )


__all__ = ["ROAD_PATH", "ALIGNMENT_PATH", "FEATURE_RESULTS_PATH", "assess_candidate_state"]
