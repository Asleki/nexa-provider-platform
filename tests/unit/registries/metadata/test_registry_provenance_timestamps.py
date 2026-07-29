from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import RegistryProvenance, RegistryProvenanceError

UTC_TIME = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)


def make(**overrides):
    values = {
        "source_type": "system",
        "source_system": "npp",
        "recorded_at": UTC_TIME,
    }
    values.update(overrides)
    return RegistryProvenance(**values)


def test_recorded_and_verified_times_are_normalised_to_utc():
    plus_two = timezone(timedelta(hours=2))
    item = make(
        recorded_at=datetime(2026, 7, 29, 12, 0, tzinfo=plus_two),
        verified=True,
        verified_at=datetime(2026, 7, 29, 13, 0, tzinfo=plus_two),
    )
    assert item.recorded_at == UTC_TIME
    assert item.verified_at == datetime(2026, 7, 29, 11, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["recorded_at", "verified_at"])
def test_naive_timestamps_are_rejected(field):
    overrides = {field: datetime(2026, 7, 29, 10, 0)}
    if field == "verified_at":
        overrides["verified"] = True
    with pytest.raises(RegistryProvenanceError, match="timezone-aware"):
        make(**overrides)


def test_verified_provenance_requires_time_or_reference():
    with pytest.raises(RegistryProvenanceError, match="requires verified_at"):
        make(verified=True)


def test_unverified_provenance_rejects_verification_details():
    with pytest.raises(RegistryProvenanceError, match="cannot contain verification details"):
        make(verification_reference="VERIFY-1")


def test_verification_cannot_precede_provenance_recording():
    with pytest.raises(RegistryProvenanceError, match="cannot be earlier"):
        make(
            verified=True,
            verified_at=UTC_TIME - timedelta(seconds=1),
        )


def test_future_aware_timestamps_are_not_rejected_by_the_contract():
    future = datetime(2099, 1, 1, tzinfo=timezone.utc)
    assert make(recorded_at=future).recorded_at == future


def test_from_dict_accepts_z_suffix_and_iso_offset_timestamps():
    item = RegistryProvenance.from_dict(
        {
            "source_type": "system",
            "source_system": "npp",
            "recorded_at": "2026-07-29T10:00:00Z",
            "verified": True,
            "verified_at": "2026-07-29T12:30:00+02:00",
        }
    )
    assert item.recorded_at == UTC_TIME
    assert item.verified_at == datetime(2026, 7, 29, 10, 30, tzinfo=timezone.utc)


@pytest.mark.parametrize("field", ["recorded_at", "verified_at"])
def test_from_dict_rejects_invalid_iso_timestamps(field):
    data = {
        "source_type": "system",
        "source_system": "npp",
        "recorded_at": UTC_TIME.isoformat(),
        field: "not-a-time",
    }
    if field == "verified_at":
        data["verified"] = True
    with pytest.raises(RegistryProvenanceError, match="valid ISO datetime"):
        RegistryProvenance.from_dict(data)
