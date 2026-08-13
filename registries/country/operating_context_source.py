"""Governed Bundle 13B migration-source reader.

This reader is allowed for qualification, migration and tests only. Live
application authority must later be persisted in PostgreSQL and must not query
these CSV snapshots as runtime storage.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from shared.runtime.operation_runtime import OperationRuntimeMode
from .locale_currency_boundary import CurrencyReferenceBoundary, LocaleReferenceBoundary
from .operating_context import (
    ApprovalState,
    RecordEffectScope,
    ReferenceLifecycleStatus,
    RuntimeReference,
    WorldRealmReference,
)
from .temporal_context import (
    CalendarReference,
    DateTimeFormatPolicy,
    RuntimeTimeMapping,
    TimezoneReference,
)


@dataclass(frozen=True, slots=True)
class Bundle13BSourceSnapshot:
    realm: WorldRealmReference
    runtimes: tuple[RuntimeReference, ...]
    effect_scopes: tuple[RecordEffectScope, ...]
    approval_states: tuple[ApprovalState, ...]
    timezone: TimezoneReference
    runtime_time_mappings: tuple[RuntimeTimeMapping, ...]
    calendar: CalendarReference
    date_time_policy: DateTimeFormatPolicy
    locale: LocaleReferenceBoundary
    currency: CurrencyReferenceBoundary


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} has no header.")
        return list(reader)


def _single(path: Path) -> dict[str, str]:
    rows = _rows(path)
    if len(rows) != 1:
        raise ValueError(f"{path.name} must contain exactly one row.")
    return rows[0]


def _active(value: str) -> ReferenceLifecycleStatus:
    return ReferenceLifecycleStatus(value.strip().upper())


def read_bundle13b_source(repository_root: str | Path) -> Bundle13BSourceSnapshot:
    root = Path(repository_root)
    source = root / "data/novegeo/country/operating-context/source"
    country_profile = root / "data/novegeo/country/source/novegeo_country_profile.csv"
    if not source.is_dir():
        raise FileNotFoundError(source)

    realm_row = _single(source / "nexilabs_world_realm_register.csv")
    realm = WorldRealmReference(
        realm_id=realm_row["world_realm_id"],
        realm_code=realm_row["realm_code"],
        realm_name=realm_row["realm_name"],
        realm_type=realm_row["realm_type"],
        country_id=realm_row["country_record_id"],
        status=_active(realm_row["status"]),
        effective_from=date.fromisoformat(realm_row["effective_from"]),
    )

    runtime_rows = _rows(source / "nexilabs_application_runtime_register.csv")
    runtimes = tuple(
        RuntimeReference(
            runtime_mode=OperationRuntimeMode(row["runtime_code"].lower()),
            canonical_label=row["canonical_label"],
            semantic_role=row["semantic_role"],
            status=_active(row["status"]),
            effective_from=date.fromisoformat(row["effective_from"]),
        )
        for row in runtime_rows
    )

    effect_scopes = tuple(
        RecordEffectScope(row["effect_scope_code"].strip().upper())
        for row in _rows(source / "nexilabs_record_effect_scope_register.csv")
        if row["status"].strip().upper() == "ACTIVE"
    )
    approval_states = tuple(
        ApprovalState(row["approval_state_code"].strip().upper())
        for row in _rows(source / "nexilabs_approval_state_register.csv")
        if row["status"].strip().upper() == "ACTIVE"
    )

    timezone_row = _single(source / "novegeo_timezone_definition.csv")
    timezone = TimezoneReference(
        timezone_code=timezone_row["timezone_code"],
        iana_name=timezone_row["iana_name"],
        utc_offset_standard=timezone_row["utc_offset_standard"],
        dst_observed=timezone_row["dst_observed"].strip().lower() == "true",
        canonical_label=timezone_row["canonical_label"],
        status=_active(timezone_row["status"]),
    )

    runtime_time_mappings = tuple(
        RuntimeTimeMapping(
            mapping_id=row["mapping_id"],
            runtime_mode=OperationRuntimeMode(row["runtime_code"].lower()),
            timezone_code=row["timezone_code"],
            clock_ratio=row["clock_ratio"],
            calendar_code=row["calendar_code"],
            status=_active(row["status"]),
        )
        for row in _rows(source / "novegeo_runtime_timezone_mapping.csv")
    )

    calendar_row = _single(source / "novegeo_calendar_definition.csv")
    calendar = CalendarReference(
        calendar_code=calendar_row["calendar_code"],
        canonical_name=calendar_row["canonical_name"],
        calendar_system=calendar_row["calendar_system"],
        days_per_week=int(calendar_row["days_per_week"]),
        month_model=calendar_row["month_model"],
        leap_year_model=calendar_row["leap_year_model"],
        status=_active(calendar_row["status"]),
    )

    policy_row = _single(source / "novegeo_date_time_format_policy.csv")
    policy = DateTimeFormatPolicy(
        policy_id=policy_row["policy_id"],
        date_format=policy_row["date_format"],
        time_format=policy_row["time_format"],
        datetime_format=policy_row["datetime_format"],
        first_day_of_week=policy_row["first_day_of_week"],
        status=_active(policy_row["status"]),
    )

    country = _single(country_profile)
    locale = LocaleReferenceBoundary(
        timezone_code=country["default_timezone_code"],
        calendar_code=country["calendar_code"],
        date_time_policy_id=policy.policy_id,
        status=country["status"],
    )
    currency = CurrencyReferenceBoundary(
        currency_code=country["currency_code"],
        currency_symbol=country["currency_symbol"],
        country_id=country["country_record_id"],
        status=country["status"],
    )

    return Bundle13BSourceSnapshot(
        realm=realm,
        runtimes=runtimes,
        effect_scopes=effect_scopes,
        approval_states=approval_states,
        timezone=timezone,
        runtime_time_mappings=runtime_time_mappings,
        calendar=calendar,
        date_time_policy=policy,
        locale=locale,
        currency=currency,
    )
