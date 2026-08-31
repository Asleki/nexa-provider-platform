"""Deterministic identifiers and canonical hashes for MUNICIPALITY realization."""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .contracts import PLAN_ID, PLAN_VERSION


def normalize_effective_date(value: str | None = None) -> str:
    return date.fromisoformat(str(value or date.today().isoformat()).strip()).isoformat()


def municipality_geometry_id(municipality_id: str) -> str:
    return f"municipality-geometry:nngla:{municipality_id}:v1"


def municipality_publication_id(municipality_id: str) -> str:
    return f"municipality-publication:nngla:{municipality_id}:v1"


def partition_qualification_id(region_id: str) -> str:
    return f"municipality-partition:nngla:{region_id}:v1"


def execution_id(fingerprint: str) -> str:
    return f"nnglarun:municipality-realization:{fingerprint}"


def canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def member_set_payload(items) -> tuple[dict[str, str], ...]:
    return tuple(
        sorted(
            (
                {
                    "municipalityId": str(item["municipalityId"]),
                    "geometryId": str(item["geometryId"]),
                    "geometrySha256": str(item["geometrySha256"]),
                }
                for item in items
            ),
            key=lambda item: item["municipalityId"],
        )
    )


def fingerprint_payload(payload: dict[str, object]) -> str:
    return canonical_sha256({"planId": PLAN_ID, "planVersion": PLAN_VERSION, **payload})
