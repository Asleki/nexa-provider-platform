from datetime import timedelta

import pytest

from registries.metadata import RegistryRetention, RegistryRetentionError


def test_positive_whole_second_period_is_preserved_and_serialized():
    item = RegistryRetention(
        "fixed_duration",
        "Temporary record",
        retention_period=timedelta(seconds=90),
    )
    assert item.retention_period == timedelta(seconds=90)
    assert item.to_dict()["retention_seconds"] == 90


@pytest.mark.parametrize("period", [timedelta(0), timedelta(seconds=-1)])
def test_non_positive_periods_are_rejected(period):
    with pytest.raises(RegistryRetentionError, match="must be positive"):
        RegistryRetention("fixed_duration", "Temporary", retention_period=period)


def test_fractional_second_period_is_rejected_instead_of_truncated():
    with pytest.raises(RegistryRetentionError, match="whole-second precision"):
        RegistryRetention(
            "fixed_duration",
            "Temporary",
            retention_period=timedelta(seconds=1, microseconds=1),
        )


def test_period_requires_timedelta():
    with pytest.raises(TypeError, match="must be a timedelta"):
        RegistryRetention("fixed_duration", "Temporary", retention_period=30)


def test_event_triggered_period_means_elapsed_time_after_trigger():
    item = RegistryRetention(
        "event_triggered",
        "Account evidence",
        trigger_event="ACCOUNT_CLOSED",
        retention_period=timedelta(days=365 * 7),
    )
    assert item.trigger_event == "ACCOUNT_CLOSED"
    assert item.to_dict()["retention_seconds"] == 365 * 7 * 86400


def test_large_exact_duration_remains_valid():
    period = timedelta(days=365 * 100)
    assert RegistryRetention(
        "fixed_duration",
        "Historical technical policy",
        retention_period=period,
    ).retention_period == period
