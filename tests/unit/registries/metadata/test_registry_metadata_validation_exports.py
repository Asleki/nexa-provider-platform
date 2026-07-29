from registries.metadata import InvalidRegistryMetadataError, RegistryMetadataValidator


def test_validation_contracts_are_publicly_exported():
    assert RegistryMetadataValidator.VERSION == 1
    assert issubclass(InvalidRegistryMetadataError, ValueError)
