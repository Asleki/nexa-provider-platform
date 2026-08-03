from pathlib import Path

def test_migration_defines_additive_reference_objects():
    text=Path('database/migrations/m009_13_10_reference_registry_authoring.sql').read_text()
    for token in ('reference.reference_authority_record','reference.name_orthography_profile','reference.name_context_relationship','reference.tribe_code_seq','accent_stripping_authorized=false'):
        assert token in text
    assert 'DROP TABLE' not in text

def test_reset_is_not_embedded_in_migration():
    text=Path('database/migrations/m009_13_10_reference_registry_authoring.sql').read_text()
    assert 'DELETE FROM reference.canonical_name' not in text
