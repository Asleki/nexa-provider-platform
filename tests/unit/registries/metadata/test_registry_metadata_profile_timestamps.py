from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import RegistryMetadataProfileError
from tests.unit.registries.metadata.metadata_test_support import make_profile


def test_profile_normalises_aware_timestamps_to_utc():
    offset = timezone(timedelta(hours=3))
    profile = make_profile(effective_from=datetime(2026, 7, 29, 11, 0, tzinfo=offset))
    assert profile.effective_from == datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["effective_from", "reviewed_at"])
def test_profile_rejects_naive_timestamps(field):
    kwargs = {field: datetime(2026, 7, 29, 8, 0)}
    if field == "reviewed_at":
        kwargs["review_status"] = "approved"
    with pytest.raises(RegistryMetadataProfileError, match="timezone-aware"):
        make_profile(**kwargs)


def test_review_may_precede_a_future_effective_date():
    profile = make_profile(
        effective_from=datetime(2026, 9, 1, tzinfo=timezone.utc),
        reviewed_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        review_status="approved",
    )
    assert profile.reviewed_at < profile.effective_from
