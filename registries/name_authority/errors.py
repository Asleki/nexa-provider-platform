"""Stable M009.12 seed activation and governed import errors."""
class NameAuthoritySeedError(Exception):
    code = "NAME_AUTHORITY_SEED_ERROR"
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class SeedManifestError(NameAuthoritySeedError): code = "NAME_SEED_MANIFEST_INVALID"
class SeedPathError(NameAuthoritySeedError): code = "NAME_SEED_PATH_UNSAFE"
class SeedIntegrityError(NameAuthoritySeedError): code = "NAME_SEED_INTEGRITY_FAILED"
class SeedAdapterError(NameAuthoritySeedError): code = "NAME_SEED_ADAPTER_FAILED"
class SeedRuntimeError(NameAuthoritySeedError): code = "NAME_SEED_RUNTIME_INVALID"
class SeedRelationshipError(NameAuthoritySeedError): code = "NAME_SEED_RELATIONSHIP_INVALID"
class SeedSourceNotAtomicError(NameAuthoritySeedError): code = "NAME_SEED_SOURCE_NOT_ATOMIC_NAME"
__all__=["NameAuthoritySeedError","SeedManifestError","SeedPathError","SeedIntegrityError","SeedAdapterError","SeedRuntimeError","SeedRelationshipError","SeedSourceNotAtomicError"]
