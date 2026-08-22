"""Immutable initial administrative-boundary legalization decisions."""
from __future__ import annotations
from functools import lru_cache
from ._shared import LEGALIZATION_DECISIONS,EXPECTED_COUNT,csv_rows
from .source import load_administrative_baseline
@lru_cache(maxsize=1)
def load_legalization_decisions():
    rows=csv_rows(LEGALIZATION_DECISIONS); ids={r['administrative_area_id'] for r in load_administrative_baseline()}
    if len(rows)!=EXPECTED_COUNT or {r['administrative_area_id'] for r in rows}!=ids: raise ValueError('exactly 192 legalization decisions required')
    for r in rows:
        if r['decision_status']!='APPROVED_FOR_GOVERNED_LIVE_APPLICATION' or r['previous_boundary_status']!='BOUNDARY_PENDING_LEGALIZATION' or r['resulting_boundary_status']!='LEGALIZED' or r['previous_lifecycle_status']!='PROVISIONAL' or r['resulting_lifecycle_status']!='ACTIVE': raise ValueError('illegal initial legalization transition')
    return rows
