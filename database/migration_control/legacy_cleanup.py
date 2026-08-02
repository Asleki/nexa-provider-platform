"""Strict one-time cleanup of explicitly allowed empty development schemas."""
from __future__ import annotations
from dataclasses import dataclass
from .errors import MigrationCleanupError

LEGACY_SCHEMA_ALLOWLIST=frozenset({'audit','identity','integration','reference','registry','simulation'})
PROTECTED_SCHEMAS=frozenset({'public','pg_catalog','information_schema','platform'})

@dataclass(frozen=True, slots=True)
class CleanupResult:
    dropped_schemas: tuple[str, ...]

class LegacySchemaCleanupService:
    def __init__(self, adapter, ledger): self.adapter=adapter; self.ledger=ledger
    def prepare_development_target(self, *, database_name, environment_name, schemas, confirmed=False):
        if environment_name!='development' or database_name!='npp_dev': raise MigrationCleanupError('Legacy cleanup is allowed only for development database npp_dev.')
        if self.ledger.is_bootstrapped() and self.ledger.history(): raise MigrationCleanupError('Legacy cleanup is blocked after migration history exists.')
        requested=tuple(dict.fromkeys(schemas))
        if not requested or any(s not in LEGACY_SCHEMA_ALLOWLIST or s in PROTECTED_SCHEMAS for s in requested): raise MigrationCleanupError('Cleanup request contains a schema outside the exact legacy allowlist.')
        if not confirmed: raise MigrationCleanupError('Legacy cleanup requires explicit confirmation.')
        for schema in requested:
            inventory=self.adapter.inspect_schema_inventory(schema)
            if not inventory.is_empty: raise MigrationCleanupError(f'Legacy schema {schema} is not empty.')
        for schema in requested: self.adapter.drop_empty_schema(schema)
        return CleanupResult(requested)
