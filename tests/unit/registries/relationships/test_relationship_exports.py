import registries.relationships as relationships


def test_relationship_package_exports_contract_family():
    expected = {
        "RegistryReference",
        "RegistryReferenceError",
        "RelationshipType",
        "RelationshipTypeError",
        "RelationshipDefinition",
        "RelationshipDefinitionError",
    }
    assert expected <= set(relationships.__all__)
    for name in expected:
        assert getattr(relationships, name) is not None
