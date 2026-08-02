from database.migration_control.legacy_cleanup import LEGACY_SCHEMA_ALLOWLIST
from database.migration_control.qualification import MigrationQualificationService

def test_legacy_allowlist_is_exact_and_qualification_sequence_is_readable():
    assert LEGACY_SCHEMA_ALLOWLIST==frozenset({'audit','identity','integration','reference','registry','simulation'})
    assert MigrationQualificationService.STEPS[0]=='inspect-target'
    assert 'verify-expected-objects' in MigrationQualificationService.STEPS
