import pytest
from registries.metadata import RegistryClassificationLevel, RegistryDataClassification, RegistryClassificationError

def test_levels_are_ordered_and_classification_serializes():
    assert RegistryClassificationLevel.PUBLIC < RegistryClassificationLevel.HIGHLY_RESTRICTED
    item = RegistryDataClassification("restricted", "Citizen identity", contains_personal_data=True, masking_required=True)
    assert item.level is RegistryClassificationLevel.RESTRICTED
    assert item.to_dict()["level"] == "restricted"

def test_confidential_data_cannot_be_publicly_disclosed():
    with pytest.raises(RegistryClassificationError): RegistryDataClassification("confidential", "Private", public_disclosure_allowed=True)
