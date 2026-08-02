"""Sanitized human and JSON formatting."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum


def _clean(value):
    """Convert migration-control values into deterministic JSON-safe data.

    Dataclasses are traversed field-by-field instead of through
    ``dataclasses.asdict``.  This preserves immutable contract values such as
    ``MappingProxyType`` without attempting a recursive deep copy.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _clean(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_clean(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_clean(item) for item in sorted(value, key=repr)]
    if isinstance(value, Enum):
        return _clean(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def format_json(value):
    return json.dumps(_clean(value), sort_keys=True, indent=2)


def format_status(status):
    return "\n".join(
        [
            f"Ledger state: {status.ledger_state}",
            f"Repository migrations: {status.repository_migrations}",
            f"Applied migrations: {status.applied_migrations}",
            f"Pending migrations: {status.pending_migrations}",
            f"Failed migrations: {status.failed_migrations}",
            f"Started migrations: {status.started_migrations}",
            f"Checksum mismatches: {status.checksum_mismatches}",
            f"Unknown database migrations: {status.unknown_database_migrations}",
            f"Plan checksum: {status.plan_checksum}",
        ]
    )
