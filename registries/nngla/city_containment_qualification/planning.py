"""Deterministic identifiers/fingerprints for P006.7.11.15.8.1."""
from __future__ import annotations

from hashlib import sha256
import json

from .contracts import CONTAINMENT_PLAN_ID, CONTAINMENT_PLAN_VERSION


def _sha(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def qualification_id(
    *,
    city_id: str,
    city_geometry_id: str,
    parent_region_geometry_id: str,
    qualification_policy_version: int,
) -> str:
    if qualification_policy_version < 1:
        raise ValueError("qualification_policy_version must be positive")
    digest = _sha(
        {
            "cityId": str(city_id),
            "cityGeometryId": str(city_geometry_id),
            "parentRegionGeometryId": str(parent_region_geometry_id),
            "qualificationPolicyVersion": qualification_policy_version,
        }
    )[:24]
    return f"city-containment:nngla:{city_id}:{digest}"


def qualification_fingerprint(payload: dict[str, object]) -> str:
    governed = {
        "planId": CONTAINMENT_PLAN_ID,
        "planVersion": CONTAINMENT_PLAN_VERSION,
        **payload,
    }
    return _sha(governed)


def execution_id(fingerprint: str) -> str:
    text = str(fingerprint)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError("fingerprint must be lowercase SHA-256")
    return f"nnglarun:city-containment-qualification:{text}"
