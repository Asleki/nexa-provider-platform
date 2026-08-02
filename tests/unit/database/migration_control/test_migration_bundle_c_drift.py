from database.migration_control.drift import *

def test_drift_reports_missing_expected_objects():
    expected=type('E',(),{'schemas':('reference',),'tables':('reference.names',),'indexes':(),'constraints':(),'views':(),'functions':()})()
    d=type('D',(),{'expected_objects':expected})()
    p=type('P',(),{'forward_order':(d,)})()
    class A:
        def inspect_database_objects(self): return DatabaseObjectState(schemas=frozenset({'reference'}))
    r=MigrationDriftInspector(A()).inspect_expected(p)
    assert r.missing==('table:reference.names',)

def test_inventory_counts_every_supported_object_type():
    assert SchemaInventory('x').is_empty
    assert not SchemaInventory('x',custom_types=1).is_empty
