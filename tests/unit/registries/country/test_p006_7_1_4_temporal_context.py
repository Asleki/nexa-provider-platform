from datetime import timedelta

import pytest

from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.temporal_context import (
    CalendarReference,
    DateTimeFormatPolicy,
    FirstDayOfWeek,
    RuntimeTimeMapping,
    TimezoneReference,
)


def test_p006_7_1_4_novegeo_timezone_preserves_identity_and_executable_fixed_offset():
    reference = TimezoneReference(
        timezone_code="Africa/NoveGeo",
        iana_name="Africa/NoveGeo",
        utc_offset_standard="+02:00",
        dst_observed=False,
        canonical_label="NoveGeo Central Africa Time",
    )
    assert reference.timezone_code == "Africa/NoveGeo"
    assert reference.dst_observed is False
    assert reference.fixed_offset.utcoffset(None) == timedelta(hours=2)
    assert reference.fixed_offset.tzname(None) == "Africa/NoveGeo"


def test_p006_7_1_4_both_semantic_runtimes_use_one_to_one_novegeo_clock():
    simulation = RuntimeTimeMapping("rtz:simulation", "simulation", "Africa/NoveGeo", "1:1", "GREGORIAN")
    production = RuntimeTimeMapping("rtz:production", "production", "Africa/NoveGeo", "1:1", "GREGORIAN")
    assert simulation.runtime_mode is OperationRuntimeMode.SIMULATION
    assert production.runtime_mode is OperationRuntimeMode.PRODUCTION
    assert simulation.clock_ratio_value == 1.0
    assert production.clock_ratio_value == 1.0


def test_p006_7_1_4_gregorian_and_local_presentation_policy_are_reference_contracts():
    calendar = CalendarReference("GREGORIAN", "Gregorian Calendar", "Gregorian", 7, "12_months", "Gregorian")
    policy = DateTimeFormatPolicy(
        "dtpolicy:novegeo:v1",
        "DD/MM/YYYY",
        "HH:mm:ss",
        "DD/MM/YYYY HH:mm:ss",
        "MONDAY",
    )
    assert calendar.days_per_week == 7
    assert calendar.month_model == "12_months"
    assert policy.first_day_of_week is FirstDayOfWeek.MONDAY
    assert policy.datetime_format == "DD/MM/YYYY HH:mm:ss"


def test_p006_7_1_4_rejects_invalid_offsets_and_clock_ratios():
    with pytest.raises(ValueError):
        TimezoneReference("Africa/NoveGeo", "Africa/NoveGeo", "+2", False, "NoveGeo")
    with pytest.raises(ValueError):
        RuntimeTimeMapping("rtz:simulation", "simulation", "Africa/NoveGeo", "0:1", "GREGORIAN")
