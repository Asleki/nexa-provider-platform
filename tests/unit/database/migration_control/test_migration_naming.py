import pytest

from database.migration_control.errors import MigrationIdentityError
from database.migration_control.naming import parse_migration_filename, validate_filename_identity


def test_forward_filename_maps_zero_padded_segments_to_roadmap_identity():
    parsed = parse_migration_filename("m009_12_06_name_authority.sql")
    assert parsed.migration_id == "m009_12_06_name_authority"
    assert parsed.milestone_id == "M009.12.6"
    assert parsed.direction == "forward"
    assert (parsed.parent_segment, parsed.minor_segment, parsed.leaf_segment) == (9, 12, 6)


def test_rollback_filename_preserves_forward_migration_identity():
    parsed = parse_migration_filename("m009_12_06_name_authority_rollback.sql")
    assert parsed.migration_id == "m009_12_06_name_authority"
    assert parsed.direction == "rollback"


@pytest.mark.parametrize(
    "filename",
    [
        "m9_12_06_name_authority.sql",
        "m009_12_6_name_authority.sql",
        "M009_12_06_name_authority.sql",
        "m009_12_06_Name_Authority.sql",
        "m009_12_06_name-authority.sql",
        "m009_12_06_name_authority.sql.bak",
        "temporary.sql",
        "../m009_12_06_name_authority.sql",
    ],
)
def test_invalid_filename_grammar_is_rejected(filename):
    with pytest.raises(MigrationIdentityError):
        parse_migration_filename(filename)


def test_manifest_and_filename_identity_must_agree():
    with pytest.raises(MigrationIdentityError):
        validate_filename_identity(
            "m009_12_06_name_authority.sql",
            expected_migration_id="m009_12_09_name_authority_generation",
            expected_milestone_id="M009.12.6",
            expected_direction="forward",
        )
