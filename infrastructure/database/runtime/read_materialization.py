"""P006.7.11.15.10.1.2 request-scoped read materialization primitives.

Materialized values are ephemeral request-local copies of already-authorized
read facts.  They never replace PostgreSQL authority and they are deliberately
unavailable outside an active ``PostgreSQLPool.read_session()``.
"""
from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from typing import Any


class RequestReadMaterialization:
    """Opaque request-local values and subject-indexed record materialization."""

    def __init__(self) -> None:
        self._values: dict[Hashable, object] = {}

    def get(self, key: Hashable, default: object = None) -> object:
        return self._values.get(key, default)

    def set(self, key: Hashable, value: object) -> object:
        self._values[key] = value
        return value

    def merge_mapping(self, key: Hashable, values: Mapping[str, object]) -> None:
        current = self._values.get(key)
        merged: dict[str, object] = dict(current) if isinstance(current, dict) else {}
        merged.update({str(subject_id): value for subject_id, value in values.items()})
        self._values[key] = merged

    def complete_mapping(
        self,
        key: Hashable,
        subject_ids: Iterable[str],
    ) -> dict[str, object] | None:
        wanted = tuple(dict.fromkeys(str(subject_id) for subject_id in subject_ids))
        current = self._values.get(key)
        if not isinstance(current, dict):
            return None
        if any(subject_id not in current for subject_id in wanted):
            return None
        return {subject_id: current[subject_id] for subject_id in wanted}


def materialization_key(runtime_mode: str, namespace: str) -> tuple[str, str, str]:
    runtime = str(runtime_mode).strip().lower()
    name = str(namespace).strip()
    if not runtime or not name:
        raise ValueError("runtime_mode and namespace are required")
    return ("request-read-materialization", runtime, name)


def current_request_read_materialization(pool: Any) -> RequestReadMaterialization | None:
    """Return the pool's active materialization without requiring fake pools to implement it."""
    getter = getattr(pool, "current_read_materialization", None)
    if not callable(getter):
        return None
    materialization = getter()
    if materialization is None:
        return None
    if not isinstance(materialization, RequestReadMaterialization):
        raise TypeError("current read materialization has an unsupported type")
    return materialization


__all__ = [
    "RequestReadMaterialization",
    "current_request_read_materialization",
    "materialization_key",
]
