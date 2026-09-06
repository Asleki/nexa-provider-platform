from __future__ import annotations

import json
from pathlib import Path

from backend.auth.enigma_catalogue_admission.source import DEFAULT_SOURCE_SPECS


PREDECESSOR_MIGRATION_ID = "m006_10_02_nexilabs_account_credential_authority"
PREDECESSOR_FORWARD_SHA256 = "f26c57fb03d5d516d3f2adba4638cc44521f795833d4ab02a82c211a5f5f3e9c"
PREDECESSOR_FORWARD_BYTES = 14563


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database" / "migrations" / "migration_manifest.json").is_file():
            return candidate
    raise AssertionError("repository root not found")


def test_b_uses_frozen_private_source_hash_contract_without_committing_source_bytes() -> None:
    assert tuple(spec.word_length for spec in DEFAULT_SOURCE_SPECS) == (3, 4, 5)
    assert tuple(spec.catalogue_version for spec in DEFAULT_SOURCE_SPECS) == (1, 1, 1)
    assert tuple(spec.source_reference for spec in DEFAULT_SOURCE_SPECS) == (
        "development/auth/private/enigma/enigma_words_3.csv",
        "development/auth/private/enigma/enigma_words_4.csv",
        "development/auth/private/enigma/enigma_words_5.csv",
    )
    assert tuple(spec.expected_sha256 for spec in DEFAULT_SOURCE_SPECS) == (
        "aff0a9324d273dfe5c67c9c05421308b250e56b59c5bbeb1faa1fc8764e16fa8",
        "481c59c836e84d797b5cd1c1633618551d8329575be542c8f426a14e088dc1a0",
        "ca003d38352b5b6f348000608cf7b0a6f70f8e42557735b85aaaa2d8b981fa9e",
    )


def test_b_keeps_migration_31_immutable_when_later_migrations_append() -> None:
    """Compatibility maintenance: B had no schema growth; migration 31 need not remain tail."""
    root = _root()
    manifest = json.loads(
        (root / "database" / "migrations" / "migration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["catalogue_version"] >= 15
    assert len(manifest["migrations"]) >= 31
    row = next(
        item for item in manifest["migrations"]
        if item["migration_id"] == PREDECESSOR_MIGRATION_ID
    )
    assert row["sequence_number"] == 31
    assert row["forward_sha256"] == PREDECESSOR_FORWARD_SHA256
    assert row["forward_byte_size"] == PREDECESSOR_FORWARD_BYTES


def test_b_sql_write_path_never_stores_profile_lookup_word_in_shared_catalogue_tables() -> None:
    root = _root()
    postgresql_module = (
        root
        / "backend"
        / "auth"
        / "enigma_catalogue_admission"
        / "postgresql.py"
    ).read_text(encoding="utf-8")
    assert "profile_lookup_word" not in postgresql_module
    assert "INSERT INTO nexilabs_auth.enigma_catalogue_entry" in postgresql_module
    assert "word_1" in postgresql_module
    assert "word_2" in postgresql_module
    assert "word_3" in postgresql_module
