"""Canonical root selection for governed spatial realization batches."""
from __future__ import annotations

from hashlib import sha256
import json
import re
from collections.abc import Iterable

from .source import city_root_by_id, city_roots

_PLACE_ID = re.compile(r"^NG-PLC-\d{6}$")


def eligible_city_root_ids() -> tuple[str, ...]:
    return tuple(root.place_id for root in city_roots())


def normalize_city_root_ids(root_ids: Iterable[str]) -> tuple[str, ...]:
    raw = tuple(str(value).strip() for value in root_ids)
    if not raw:
        raise ValueError("at least one major-city root is required")
    if len(raw) > 8:
        raise ValueError("current NoveGeo city realization accepts at most eight major-city roots")
    if any(_PLACE_ID.fullmatch(value) is None for value in raw):
        raise ValueError("city selection requires canonical NG-PLC identities")
    if len(set(raw)) != len(raw):
        raise ValueError("DUPLICATE_EXECUTION_ROOT")
    eligible = city_root_by_id()
    unknown = tuple(sorted(set(raw) - set(eligible)))
    if unknown:
        raise ValueError("UNKNOWN_OR_NON_CITY_EXECUTION_ROOT:" + ",".join(unknown))
    return tuple(sorted(raw, key=lambda value: int(value.rsplit("-", 1)[1])))


def selection_digest(normalized_root_ids: Iterable[str]) -> str:
    ids = tuple(normalized_root_ids)
    normalized = normalize_city_root_ids(ids)
    payload = json.dumps(normalized, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


__all__ = ["eligible_city_root_ids", "normalize_city_root_ids", "selection_digest"]
