import registries.catalogues as catalogues


def test_catalogue_package_exports_only_approved_public_symbols():
    assert set(catalogues.__all__) == {
        "CatalogueConflictError",
        "CatalogueNotFoundError",
        "CatalogueValidationError",
        "IdentifierCatalogue",
        "NamespaceCatalogue",
        "RegistryCatalogue",
    }
    for name in catalogues.__all__:
        assert hasattr(catalogues, name)
