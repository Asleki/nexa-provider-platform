import registries.core as core


def test_existing_core_exports_remain_available():
    required = {
        "DEFAULT_REGISTRY_DEFINITION_VERSION",
        "RegistryDefinition",
        "RegistryDefinitionError",
        "DEFAULT_NAMESPACE_DEFINITION_VERSION",
        "NamespaceDefinition",
        "NamespaceDefinitionError",
        "DEFAULT_IDENTIFIER_CASE_SENSITIVE",
        "DEFAULT_IDENTIFIER_DEFINITION_VERSION",
        "IdentifierDefinition",
        "IdentifierDefinitionError",
        "NumberingMode",
        "NumberingStrategy",
        "NumberingStrategyError",
        "DEFAULT_IDENTIFIER_REFERENCE_VERSION",
        "IdentifierReference",
        "IdentifierReferenceError",
    }
    assert required.issubset(set(core.__all__))


def test_registry_family_and_status_are_public_core_dependencies():
    assert core.RegistryFamily.__name__ == "RegistryFamily"
    assert core.RegistryStatus.__name__ == "RegistryStatus"
    assert "RegistryFamily" in core.__all__
    assert "RegistryStatus" in core.__all__


def test_core_exports_are_unique():
    assert len(core.__all__) == len(set(core.__all__))
