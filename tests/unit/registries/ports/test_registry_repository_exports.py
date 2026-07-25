from registries import ports


def test_public_exports_are_exact_and_unique() -> None:
    assert len(ports.__all__) == len(set(ports.__all__))
    assert set(ports.__all__) == {
        "REGISTRY_REPOSITORY_ERROR_PREFIX",
        "BaseRegistryRepository",
        "RegistryAddError",
        "RegistryClearError",
        "RegistryCountError",
        "RegistryDuplicateError",
        "RegistryExistsError",
        "RegistryIdentifierError",
        "RegistryInvalidRecordError",
        "RegistryListError",
        "RegistryNotFoundError",
        "RegistryReadError",
        "RegistryRecordError",
        "RegistryRemoveError",
        "RegistryReplaceError",
        "RegistryRepositoryConfigurationError",
        "RegistryRepositoryError",
        "RegistryRepositoryInterface",
        "RegistryRepositoryOperation",
        "RegistryRepositoryOperationError",
        "RegistryRepositoryResult",
        "RegistryStorageError",
        "RegistryUnsupportedOperationError",
    }


def test_future_placeholder_boundaries_are_not_exported() -> None:
    forbidden = {
        "IdentifierRepository",
        "SequenceRepository",
        "RegistryAuditPort",
        "MemoryRegistryRepository",
        "RegistryRepositoryFactory",
    }
    assert forbidden.isdisjoint(set(ports.__all__))
