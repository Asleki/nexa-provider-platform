import registries.contracts as contracts


def test_contract_package_exports_are_exact_and_deterministic():
    assert contracts.__all__ == (
        "RegistryContract",
        "RegistryContractError",
    )


def test_contract_exports_are_available():
    assert contracts.RegistryContract.__name__ == "RegistryContract"
    assert contracts.RegistryContractError.__name__ == "RegistryContractError"


def test_future_boundaries_are_not_exported():
    forbidden = {
        "RegistryRepository",
        "RegistryFactory",
        "RegistryCatalogue",
        "RegistryEvent",
        "RegistryAuditPort",
        "RegistryApiRequest",
    }
    assert forbidden.isdisjoint(set(contracts.__all__))
