"""Declared governed data products for P006.7.11.10."""
from __future__ import annotations

from ._shared import (
    ASSIGNMENTS_PATH,
    FOOTPRINTS_PATH,
    ISLAND_POLICY_PATH,
    QUALIFICATION_RESULTS_PATH,
    REFERENCE_POINTS_PATH,
    REGION_ANCHOR_POLICY_PATH,
    RELATIONSHIPS_PATH,
    SETTLEMENT_POLICY_PATH,
    SOURCE_HASHES_PATH,
    SUMMARY_PATH,
)

CONTROLLED_ARTIFACTS = (REGION_ANCHOR_POLICY_PATH, SETTLEMENT_POLICY_PATH, ISLAND_POLICY_PATH)
MATERIALIZED_ARTIFACTS = (
    REFERENCE_POINTS_PATH,
    FOOTPRINTS_PATH,
    RELATIONSHIPS_PATH,
    ASSIGNMENTS_PATH,
    QUALIFICATION_RESULTS_PATH,
    SOURCE_HASHES_PATH,
    SUMMARY_PATH,
)
ALL_BUNDLE_ARTIFACTS = CONTROLLED_ARTIFACTS + MATERIALIZED_ARTIFACTS


def artifact_findings() -> tuple[str, ...]:
    findings = []
    for path in CONTROLLED_ARTIFACTS:
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(f"missing-controlled-artifact:{path.name}")
    return tuple(findings)


__all__ = ["CONTROLLED_ARTIFACTS", "MATERIALIZED_ARTIFACTS", "ALL_BUNDLE_ARTIFACTS", "artifact_findings"]
