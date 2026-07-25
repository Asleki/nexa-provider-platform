import registries.core as core


def test_identifier_model_exports_are_appended_without_removing_prior_exports():
    required = {
        "RegistryFamily", "RegistryStatus", "RegistryDefinition",
        "IdentifierLifecycle", "IdentifierDefinition", "IdentifierReference",
        "NamespaceDefinition", "DEFAULT_NUMBERING_STRATEGY_VERSION",
        "NumberingMode", "NumberingStrategy",
    }
    assert required.issubset(set(core.__all__))
    assert len(core.__all__) == len(set(core.__all__))


def test_identifier_model_public_api_does_not_export_future_services():
    forbidden_fragments = ("Repository", "Validator", "Catalogue", "Audit", "Event", "Issuer")
    assert not [name for name in core.__all__ if any(x in name for x in forbidden_fragments)]
