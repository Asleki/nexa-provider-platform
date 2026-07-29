import registries.canonical as canonical

def test_public_exports_are_explicit():
    expected={"CanonicalDatasetDefinition","CanonicalDatasetDefinitionError","CanonicalDatasetReference","CanonicalDatasetReferenceError","CanonicalDatasetFinding","CanonicalDatasetRules","CanonicalDatasetValidationResult","CanonicalDatasetType","CanonicalDatasetTypeError"}
    assert set(canonical.__all__)==expected
    assert all(hasattr(canonical,name) for name in expected)
