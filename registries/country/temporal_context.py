"""P006.7.1.4 timezone, calendar and date-time reference contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone
from enum import Enum
import re

from shared.runtime.operation_runtime import OperationRuntimeMode
from .operating_context import ReferenceLifecycleStatus

_OFFSET = re.compile(r"^([+-])(\d{2}):(\d{2})$")
_RATIO = re.compile(r"^(\d+):(\d+)$")


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return " ".join(value.strip().split())


class CalendarCode(str, Enum):
    GREGORIAN = "GREGORIAN"


class FirstDayOfWeek(str, Enum):
    MONDAY = "MONDAY"


@dataclass(frozen=True, slots=True)
class TimezoneReference:
    timezone_code: str
    iana_name: str
    utc_offset_standard: str
    dst_observed: bool
    canonical_label: str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        timezone_code = _required_text(self.timezone_code, "timezone_code")
        iana_name = _required_text(self.iana_name, "iana_name")
        match = _OFFSET.fullmatch(_required_text(self.utc_offset_standard, "utc_offset_standard"))
        if match is None:
            raise ValueError("utc_offset_standard must use ±HH:MM format.")
        hours, minutes = int(match.group(2)), int(match.group(3))
        if hours > 23 or minutes > 59:
            raise ValueError("utc_offset_standard is outside the supported range.")
        if not isinstance(self.dst_observed, bool):
            raise TypeError("dst_observed must be boolean.")
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        object.__setattr__(self, "timezone_code", timezone_code)
        object.__setattr__(self, "iana_name", iana_name)
        object.__setattr__(self, "utc_offset_standard", match.group(0))
        object.__setattr__(self, "canonical_label", _required_text(self.canonical_label, "canonical_label"))
        object.__setattr__(self, "status", status)

    @property
    def fixed_offset(self) -> timezone:
        """Return executable fixed-offset semantics without requiring host tzdb."""
        match = _OFFSET.fullmatch(self.utc_offset_standard)
        assert match is not None
        sign = 1 if match.group(1) == "+" else -1
        minutes = sign * (int(match.group(2)) * 60 + int(match.group(3)))
        return timezone(timedelta(minutes=minutes), name=self.timezone_code)


@dataclass(frozen=True, slots=True)
class CalendarReference:
    calendar_code: CalendarCode | str
    canonical_name: str
    calendar_system: str
    days_per_week: int
    month_model: str
    leap_year_model: str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        code = self.calendar_code if isinstance(self.calendar_code, CalendarCode) else CalendarCode(str(self.calendar_code).upper())
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        if isinstance(self.days_per_week, bool) or not isinstance(self.days_per_week, int) or self.days_per_week <= 0:
            raise ValueError("days_per_week must be a positive integer.")
        object.__setattr__(self, "calendar_code", code)
        object.__setattr__(self, "canonical_name", _required_text(self.canonical_name, "canonical_name"))
        object.__setattr__(self, "calendar_system", _required_text(self.calendar_system, "calendar_system"))
        object.__setattr__(self, "month_model", _required_text(self.month_model, "month_model"))
        object.__setattr__(self, "leap_year_model", _required_text(self.leap_year_model, "leap_year_model"))
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class RuntimeTimeMapping:
    mapping_id: str
    runtime_mode: OperationRuntimeMode | str
    timezone_code: str
    clock_ratio: str
    calendar_code: CalendarCode | str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        mapping_id = _required_text(self.mapping_id, "mapping_id").lower()
        if not mapping_id.startswith("rtz:"):
            raise ValueError("mapping_id must use the rtz: namespace.")
        runtime = self.runtime_mode if isinstance(self.runtime_mode, OperationRuntimeMode) else OperationRuntimeMode(str(self.runtime_mode).strip().lower())
        calendar = self.calendar_code if isinstance(self.calendar_code, CalendarCode) else CalendarCode(str(self.calendar_code).upper())
        ratio = _required_text(self.clock_ratio, "clock_ratio")
        match = _RATIO.fullmatch(ratio)
        if match is None or int(match.group(1)) <= 0 or int(match.group(2)) <= 0:
            raise ValueError("clock_ratio must use positive integer N:D form.")
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        object.__setattr__(self, "mapping_id", mapping_id)
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "timezone_code", _required_text(self.timezone_code, "timezone_code"))
        object.__setattr__(self, "clock_ratio", ratio)
        object.__setattr__(self, "calendar_code", calendar)
        object.__setattr__(self, "status", status)

    @property
    def clock_ratio_value(self) -> float:
        numerator, denominator = self.clock_ratio.split(":", 1)
        return int(numerator) / int(denominator)


@dataclass(frozen=True, slots=True)
class DateTimeFormatPolicy:
    policy_id: str
    date_format: str
    time_format: str
    datetime_format: str
    first_day_of_week: FirstDayOfWeek | str
    status: ReferenceLifecycleStatus | str = ReferenceLifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        policy_id = _required_text(self.policy_id, "policy_id").lower()
        if not policy_id.startswith("dtpolicy:"):
            raise ValueError("policy_id must use the dtpolicy: namespace.")
        first_day = self.first_day_of_week if isinstance(self.first_day_of_week, FirstDayOfWeek) else FirstDayOfWeek(str(self.first_day_of_week).upper())
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "date_format", _required_text(self.date_format, "date_format"))
        object.__setattr__(self, "time_format", _required_text(self.time_format, "time_format"))
        object.__setattr__(self, "datetime_format", _required_text(self.datetime_format, "datetime_format"))
        object.__setattr__(self, "first_day_of_week", first_day)
        object.__setattr__(self, "status", status)
