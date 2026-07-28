import registries.metadata as metadata

def test_public_exports_are_explicit_and_complete():
    expected = {"RegistryCapability", "RegistryDataClassification", "RegistryTrainingEligibility", "RegistryProvenance", "RegistryRetention", "RegistryMetadataProfile", "RegistryMetadataValidator"}
    assert expected <= set(metadata.__all__)
    assert all(hasattr(metadata, name) for name in metadata.__all__)
