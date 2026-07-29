from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import RegistryRetention, RegistryRetentionError


def test_retain_until_and_review_at_are_normalised_to_utc():
    plus_two = timezone(timedelta(hours=2))
    retain_until = datetime(2030, 1, 2, 12, 0, tzinfo=plus_two)
    item = RegistryRetention("until_date", "Until expiry", retain_until=retain_until)
    assert item.retain_until == datetime(2030, 1, 2, 10, 0, tzinfo=timezone.utc)

    review = RegistryRetention(
        "policy_review_required",
        "Review required",
        review_at=retain_until,
    )
    assert review.review_at == datetime(2030, 1, 2, 10, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["retain_until", "review_at"])
def test_naive_timestamps_are_rejected(field):
    kwargs = {field: datetime(2030, 1, 1)}
    if field == "retain_until":
        kwargs.update(mode="until_date", reason="Until expiry")
    else:
        kwargs.update(mode="policy_review_required", reason="Review")
    with pytest.raises(RegistryRetentionError, match="timezone-aware"):
        RegistryRetention(**kwargs)


@pytest.mark.parametrize("field", ["retain_until", "review_at"])
def test_wrong_timestamp_types_are_rejected(field):
    kwargs = {field: 7}
    if field == "retain_until":
        kwargs.update(mode="until_date", reason="Until expiry")
    else:
        kwargs.update(mode="policy_review_required", reason="Review")
    with pytest.raises(TypeError, match="must be a datetime"):
        RegistryRetention(**kwargs)


def test_future_timestamps_are_valid_policy_declarations():
    future = datetime(2500, 1, 1, tzinfo=timezone.utc)
    assert RegistryRetention("until_date", "Long preservation", retain_until=future).retain_until == future
