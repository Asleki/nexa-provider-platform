import registries.api as api

def test_public_exports_are_available():
    for name in ("RegistryApi","RegistryApiRequest","RegistryApiResponse","RegistryApiOperation","RegistryApiContract"):
        assert hasattr(api,name)
