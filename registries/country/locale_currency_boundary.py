"""P006.7.1.5 locale and currency reference boundary for NoveGeo.

The contract intentionally exposes only source-supported sovereign references.
It is not a complete locale engine and does not own monetary policy, money
arithmetic, issuance, exchange rates, settlement or banking behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .operating_context import ReferenceLifecycleStatus
from .temporal_context import CalendarCode

_CURRENCY = re.compile(r"^[A-Z]{3}$")


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return " ".join(value.strip().split())


@dataclass(frozen=True, slots=True)
class LocaleReferenceBoundary:
    timezone_code: str
    calendar_code: CalendarCode | str
    date_time_policy_id: str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        calendar = self.calendar_code if isinstance(self.calendar_code, CalendarCode) else CalendarCode(str(self.calendar_code).upper())
        policy_id = _required_text(self.date_time_policy_id, "date_time_policy_id").lower()
        if not policy_id.startswith("dtpolicy:"):
            raise ValueError("date_time_policy_id must use the dtpolicy: namespace.")
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        object.__setattr__(self, "timezone_code", _required_text(self.timezone_code, "timezone_code"))
        object.__setattr__(self, "calendar_code", calendar)
        object.__setattr__(self, "date_time_policy_id", policy_id)
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class CurrencyReferenceBoundary:
    currency_code: str
    currency_symbol: str
    country_id: str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        code = _required_text(self.currency_code, "currency_code").upper()
        if not _CURRENCY.fullmatch(code):
            raise ValueError("currency_code must be exactly three ASCII letters.")
        country_id = _required_text(self.country_id, "country_id").lower()
        if not country_id.startswith("country:"):
            raise ValueError("country_id must use the country: namespace.")
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        object.__setattr__(self, "currency_code", code)
        object.__setattr__(self, "currency_symbol", _required_text(self.currency_symbol, "currency_symbol"))
        object.__setattr__(self, "country_id", country_id)
        object.__setattr__(self, "status", status)
