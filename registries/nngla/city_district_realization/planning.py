"""Deterministic identifiers, hashes and exact-topology guards for CITY_DISTRICT."""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .contracts import PLAN_ID, PLAN_VERSION


def normalize_effective_date(value: str | None = None) -> str:
    return date.fromisoformat(str(value or date.today().isoformat()).strip()).isoformat()


def district_geometry_id(district_id: str) -> str:
    return f"city-district-geometry:nngla:{district_id}:v1"


def district_publication_id(district_id: str) -> str:
    return f"city-district-publication:nngla:{district_id}:v1"


def partition_qualification_id(city_id: str) -> str:
    return f"city-district-partition:nngla:{city_id}:v1"


def execution_id(fingerprint: str) -> str:
    return f"nnglarun:city-district-realization:{fingerprint}"


def canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def exact_partition_sql() -> str:
    return "ST_Equals(ST_UnaryUnion(ST_Collect(d.geometry)), c.geometry)"


def build_member_set(rows) -> tuple[dict[str, str], ...]:
    return tuple(
        sorted(
            (
                {
                    "districtId": str(row["districtId"]),
                    "geometryId": str(row["geometryId"]),
                    "geometrySha256": str(row["geometrySha256"]),
                }
                for row in rows
            ),
            key=lambda row: row["districtId"],
        )
    )


def fingerprint_payload(payload: dict[str, object]) -> str:
    return canonical_sha256({"planId": PLAN_ID, "planVersion": PLAN_VERSION, **payload})


def require_complete_partition(evidence: dict[str, object]) -> None:
    required = (
        "all_valid",
        "all_non_empty",
        "all_polygonal",
        "all_covered_by_city",
        "union_equals_city",
    )
    if not all(bool(evidence.get(key)) for key in required):
        raise ValueError("CITY_DISTRICT partition is not exact/complete")
    if float(evidence.get("sibling_positive_overlap_m2", 0.0)) != 0.0:
        raise ValueError("CITY_DISTRICT sibling positive-area overlap detected")
    if int(evidence["observed_count"]) != int(evidence["expected_count"]):
        raise ValueError("CITY_DISTRICT count mismatch")
