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


def _plan_with_expected(*, indexes=(), tables=()):
    expected = type(
        'E',
        (),
        {
            'schemas': (),
            'tables': tables,
            'indexes': indexes,
            'constraints': (),
            'views': (),
            'functions': (),
        },
    )()
    definition = type('D', (), {'expected_objects': expected})()
    return type('P', (), {'forward_order': (definition,)})()


def test_unqualified_expected_index_matches_schema_qualified_postgresql_index():
    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState(
                indexes=frozenset({'reference.ix_name_authority_search'})
            )

    report = MigrationDriftInspector(A()).inspect_expected(
        _plan_with_expected(indexes=('ix_name_authority_search',))
    )

    assert report.is_clean
    assert report.missing == ()
    assert report.checked_count == 1


def test_schema_qualified_expected_index_uses_exact_match():
    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState(
                indexes=frozenset({'reference.ix_name_authority_search'})
            )

    report = MigrationDriftInspector(A()).inspect_expected(
        _plan_with_expected(indexes=('reference.ix_name_authority_search',))
    )

    assert report.is_clean


def test_genuinely_missing_index_uses_correct_singular_label():
    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState()

    report = MigrationDriftInspector(A()).inspect_expected(
        _plan_with_expected(indexes=('ix_missing',))
    )

    assert report.missing == ('index:ix_missing',)
    assert 'indexe:' not in report.missing[0]


def test_table_matching_remains_schema_qualified_and_exact():
    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState(tables=frozenset({'other.names'}))

    report = MigrationDriftInspector(A()).inspect_expected(
        _plan_with_expected(tables=('reference.names',))
    )

    assert report.missing == ('table:reference.names',)


def test_same_index_basename_in_multiple_schemas_still_satisfies_unqualified_manifest():
    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState(
                indexes=frozenset(
                    {
                        'reference.ix_shared_name',
                        'archive.ix_shared_name',
                    }
                )
            )

    report = MigrationDriftInspector(A()).inspect_expected(
        _plan_with_expected(indexes=('ix_shared_name',))
    )

    assert report.is_clean


def test_missing_results_are_deduplicated_and_deterministic():
    expected = type(
        'E',
        (),
        {
            'schemas': (),
            'tables': (),
            'indexes': ('ix_z', 'ix_a'),
            'constraints': (),
            'views': (),
            'functions': (),
        },
    )()
    definition = type('D', (), {'expected_objects': expected})()
    plan = type('P', (), {'forward_order': (definition, definition)})()

    class A:
        def inspect_database_objects(self):
            return DatabaseObjectState()

    report = MigrationDriftInspector(A()).inspect_expected(plan)

    assert report.missing == ('index:ix_a', 'index:ix_z')
    assert report.checked_count == 4
