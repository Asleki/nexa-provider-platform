"""Governed source reader for Bundle 13A migration-source qualification.

This reader is an engineering/import boundary only. Operational application
code must not query country authority from CSV; canonical runtime persistence
belongs to the later PostgreSQL authority milestone.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .contracts import (
    CountryCodeAssignment,
    CountryCodeKind,
    CountryIdentity,
    SovereigntyStatus,
    CountryLifecycleStatus,
)

_REQUIRED_COLUMNS = (
    "country_record_id",
    "country_code_sim",
    "alpha2_code",
    "official_name",
    "short_name",
    "sovereignty_status",
    "active_boundary_version",
    "status",
    "effective_from",
    "effective_to",
    "source_reference",
)


@dataclass(frozen=True, slots=True)
class CountrySourceRecord:
    identity: CountryIdentity
    alpha2: CountryCodeAssignment
    alpha3: CountryCodeAssignment
    active_boundary_version: int


def _parse_date(value: str, *, required: bool) -> date | None:
    text = value.strip()
    if not text:
        if required:
            raise ValueError("required source date is empty.")
        return None
    return date.fromisoformat(text)


def read_country_profile(path: str | Path) -> CountrySourceRecord:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("country profile CSV has no header.")
        missing = [name for name in _REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"country profile CSV is missing columns: {', '.join(missing)}")
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError("country profile CSV must contain exactly one sovereign-country row.")
    row = rows[0]
    effective_from = _parse_date(row["effective_from"], required=True)
    assert effective_from is not None
    effective_to = _parse_date(row["effective_to"], required=False)
    country_id = row["country_record_id"]
    identity = CountryIdentity(
        country_id=country_id,
        official_name=row["official_name"],
        short_name=row["short_name"],
        sovereignty_status=SovereigntyStatus(row["sovereignty_status"].strip().upper()),
        status=CountryLifecycleStatus(row["status"].strip().upper()),
        effective_from=effective_from,
        effective_to=effective_to,
        source_reference=row["source_reference"],
    )
    alpha2 = CountryCodeAssignment(
        country_id=country_id,
        code_kind=CountryCodeKind.ALPHA2,
        code_value=row["alpha2_code"],
        effective_from=effective_from,
        effective_to=effective_to,
    )
    alpha3 = CountryCodeAssignment(
        country_id=country_id,
        code_kind=CountryCodeKind.ALPHA3,
        code_value=row["country_code_sim"],
        effective_from=effective_from,
        effective_to=effective_to,
    )
    try:
        active_boundary_version = int(row["active_boundary_version"])
    except (TypeError, ValueError) as exc:
        raise ValueError("active_boundary_version must be an integer.") from exc
    if active_boundary_version < 1:
        raise ValueError("active_boundary_version must be positive.")
    return CountrySourceRecord(identity, alpha2, alpha3, active_boundary_version)
