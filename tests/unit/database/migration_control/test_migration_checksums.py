from pathlib import Path

import pytest

from database.migration_control.checksums import sha256_bytes, sha256_file, verify_checksum
from database.migration_control.errors import MigrationChecksumError


def test_checksum_uses_exact_file_bytes(tmp_path):
    first = tmp_path / "first.sql"
    second = tmp_path / "second.sql"
    first.write_bytes(b"SELECT 1;\n")
    second.write_bytes(b"SELECT 1; \n")
    assert sha256_file(first) != sha256_file(second)


def test_comment_change_changes_checksum():
    assert sha256_bytes(b"SELECT 1;\n") != sha256_bytes(b"-- comment\nSELECT 1;\n")


def test_verify_checksum_blocks_one_byte_change(tmp_path):
    path = tmp_path / "migration.sql"
    path.write_bytes(b"BEGIN;\nCOMMIT;\n")
    expected = sha256_file(path)
    path.write_bytes(b"BEGIN;\n COMMIT;\n")
    with pytest.raises(MigrationChecksumError):
        verify_checksum(path, expected)
