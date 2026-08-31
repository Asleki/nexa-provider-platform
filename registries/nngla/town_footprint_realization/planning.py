"""Deterministic identifiers, hashes and source qualification for TOWN."""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .contracts import (
    GEOMETRY_ROLE_CODE,
    LEGAL_BOUNDARY_STATUS,
    PLAN_ID,
    PLAN_VERSION,
    SOURCE_QUALIFICATION_STATUS,
)


def normalize_effective_date(value: str | None = None) -> str:
    return date.fromisoformat(str(value or date.today().isoformat()).strip()).isoformat()


def canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def town_footprint_id(place_id: str) -> str:
    return f"town-footprint:nngla:{place_id}:v1"


def qualification_id(place_id: str) -> str:
    return f"town-footprint-qualification:nngla:{place_id}:v1"


def publication_id(place_id: str) -> str:
    return f"town-publication:nngla:{place_id}:v1"


def execution_id(fingerprint: str) -> str:
    return f"nnglarun:town-footprint-realization:{fingerprint}"


def build_member_set(rows) -> tuple[dict[str, str], ...]:
    return tuple(
        sorted(
            (
                {
                    "placeId": str(row["placeId"]),
                    "footprintId": str(row["footprintId"]),
                    "geometrySha256": str(row["geometrySha256"]),
                }
                for row in rows
            ),
            key=lambda row: row["placeId"],
        )
    )


def fingerprint_payload(payload: dict[str, object]) -> str:
    return canonical_sha256({"planId": PLAN_ID, "planVersion": PLAN_VERSION, **payload})


def qualify_source(row, identity) -> bool:
    if row.place_id != identity.place_id:
        raise ValueError("TOWN identity mismatch")
    if row.canonical_name != identity.canonical_name:
        raise ValueError("TOWN canonical name mismatch")
    if row.region_code != identity.region_code:
        raise ValueError("TOWN region mismatch")
    if row.source_place_code != identity.source_place_code:
        raise ValueError("TOWN source place code mismatch")
    if row.parent_source_place_code != identity.parent_source_place_code:
        raise ValueError("TOWN parentage mismatch")
    if identity.parent_place_type_code != "MUNICIPALITY":
        raise ValueError("TOWN parent must be MUNICIPALITY")
    if row.geometry_role_code != GEOMETRY_ROLE_CODE:
        raise ValueError("TOWN geometry role changed")
    if row.qualification_status != SOURCE_QUALIFICATION_STATUS:
        raise ValueError("TOWN source qualification status changed")
    if row.legal_boundary_status != LEGAL_BOUNDARY_STATUS:
        raise ValueError("TOWN legal-boundary status changed")
    return True
