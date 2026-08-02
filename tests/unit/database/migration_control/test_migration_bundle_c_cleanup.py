import pytest
from database.migration_control.legacy_cleanup import *
from database.migration_control.ledger import MemoryMigrationLedger
from database.migration_control.errors import MigrationCleanupError
from database.migration_control.drift import SchemaInventory

class Adapter:
    def __init__(self, nonempty=()): self.nonempty=set(nonempty); self.dropped=[]
    def inspect_schema_inventory(self,s): return SchemaInventory(s,tables=1 if s in self.nonempty else 0)
    def drop_empty_schema(self,s): self.dropped.append(s)

def test_cleanup_only_exact_empty_development_schemas():
    a=Adapter(); r=LegacySchemaCleanupService(a,MemoryMigrationLedger(False)).prepare_development_target(database_name='npp_dev',environment_name='development',schemas=('audit','reference'),confirmed=True)
    assert r.dropped_schemas==('audit','reference') and a.dropped==['audit','reference']

@pytest.mark.parametrize('database,environment', [('postgres','development'),('npp_dev','production')])
def test_cleanup_rejects_wrong_target(database,environment):
    with pytest.raises(MigrationCleanupError): LegacySchemaCleanupService(Adapter(),MemoryMigrationLedger(False)).prepare_development_target(database_name=database,environment_name=environment,schemas=('audit',),confirmed=True)

def test_cleanup_rejects_nonempty_and_protected():
    with pytest.raises(MigrationCleanupError): LegacySchemaCleanupService(Adapter({'audit'}),MemoryMigrationLedger(False)).prepare_development_target(database_name='npp_dev',environment_name='development',schemas=('audit',),confirmed=True)
    with pytest.raises(MigrationCleanupError): LegacySchemaCleanupService(Adapter(),MemoryMigrationLedger(False)).prepare_development_target(database_name='npp_dev',environment_name='development',schemas=('public',),confirmed=True)
