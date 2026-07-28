from datetime import timedelta
import pytest
from registries.metadata import RegistryRetention, RegistryRetentionMode, RegistryRetentionError

def test_fixed_duration_retention_serializes_seconds():
    item = RegistryRetention("fixed_duration", "Temporary application", retention_period=timedelta(days=30), deletion_permitted=True)
    assert item.mode is RegistryRetentionMode.FIXED_DURATION
    assert item.to_dict()["retention_seconds"] == 2592000

def test_permanent_retention_cannot_permit_deletion():
    with pytest.raises(RegistryRetentionError): RegistryRetention("permanent", "Legal history", deletion_permitted=True)
