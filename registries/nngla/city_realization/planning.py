"""Deterministic plan identity helpers for governed CITY realization."""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .contracts import PLAN_ID, PLAN_VERSION


def normalize_effective_date(value: str | None = None) -> str:
    text = str(value or date.today().isoformat()).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError("effective date must be ISO YYYY-MM-DD") from exc


def city_geometry_id(city_id: str, realization_version: int = 1) -> str:
    if realization_version < 1:
        raise ValueError("realization_version must be positive")
    return f"city-geometry:nngla:{city_id}:v{realization_version}"


def city_publication_id(city_id: str, realization_version: int = 1) -> str:
    if realization_version < 1:
        raise ValueError("realization_version must be positive")
    return f"city-publication:nngla:{city_id}:v{realization_version}"


def execution_id(fingerprint: str) -> str:
    if len(fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in fingerprint):
        raise ValueError("fingerprint must be lowercase SHA-256")
    return f"nnglarun:city-realization:{fingerprint}"


def fingerprint_payload(payload: dict[str, object]) -> str:
    governed = {"planId": PLAN_ID, "planVersion": PLAN_VERSION, **payload}
    encoded = json.dumps(
        governed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
