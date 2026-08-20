from registries.nngla.migration_ready.contracts import (
    BatchProfile, BatchWindow, MigrationPreview, ReconciliationAction, ReconciliationItem,
)


def test_batch_profile_requires_exact_total():
    profile = BatchProfile("p", 11, (5, 6), "test")
    assert profile.expected_total == 11


def test_batch_profile_rejects_inexact_total():
    import pytest
    with pytest.raises(ValueError, match="exactly equal"):
        BatchProfile("p", 11, (5, 5), "test")


def test_preview_fingerprint_is_deterministic_and_target_sensitive():
    batch = BatchWindow(1, 0, 1, ("coordcand:nngla:a",))
    item = ReconciliationItem(
        "coordcand:nngla:a", "NG-SPT-000001", "NG-GEO-000022",
        ReconciliationAction.INSERT_NEW, "TARGET_IDENTITIES_AVAILABLE",
    )
    a = MigrationPreview.build(
        database_name="db", environment_name="development", profile_id="p",
        source_sha256="a" * 64, repository_revision="rev", batches=(batch,), reconciliation=(item,),
    )
    b = MigrationPreview.build(
        database_name="db", environment_name="development", profile_id="p",
        source_sha256="a" * 64, repository_revision="rev", batches=(batch,), reconciliation=(item,),
    )
    c = MigrationPreview.build(
        database_name="other", environment_name="development", profile_id="p",
        source_sha256="a" * 64, repository_revision="rev", batches=(batch,), reconciliation=(item,),
    )
    assert a.fingerprint == b.fingerprint
    assert a.fingerprint != c.fingerprint
