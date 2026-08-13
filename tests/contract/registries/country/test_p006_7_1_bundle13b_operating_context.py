from pathlib import Path

from registries.country.bundle13b_qualification import qualify_bundle13b_source

ROOT = Path(__file__).parents[4]


def test_bundle13b_validated_authority_snapshot_qualifies_without_becoming_runtime_storage():
    receipt = qualify_bundle13b_source(ROOT)
    assert receipt.status == "PASSED"
    assert "CSV_RUNTIME_AUTHORITY_PROHIBITED" in receipt.findings
    assert "POSTGRESQL_AUTHORITY_BOUNDARY_PRESERVED" in receipt.findings
    assert "BUNDLE13A_IMMUTABILITY_PRESERVED" in receipt.findings
    assert len(receipt.source_sha256) == 11
    assert all(len(digest) == 64 for _, digest in receipt.source_sha256)


def test_bundle13b_preserves_realm_runtime_effect_approval_and_time_boundaries():
    source = qualify_bundle13b_source(ROOT).source
    assert source.realm.realm_id == "realm:nexilabs:novegeo"
    assert {runtime.semantic_role for runtime in source.runtimes} == {
        "simulated_world_operations",
        "governed_operator_actions",
    }
    assert all(mapping.clock_ratio == "1:1" for mapping in source.runtime_time_mappings)
    assert source.date_time_policy.date_format == "DD/MM/YYYY"
    assert source.date_time_policy.time_format == "HH:mm:ss"
    assert source.date_time_policy.first_day_of_week.value == "MONDAY"


def test_bundle13b_does_not_modify_locked_bundle13a_contract_surface():
    contracts = (ROOT / "registries/country/contracts.py").read_text(encoding="utf-8")
    source = (ROOT / "registries/country/source.py").read_text(encoding="utf-8")
    qualification = (ROOT / "registries/country/qualification.py").read_text(encoding="utf-8")
    assert "Bundle 13A" in contracts
    assert "Bundle 13A" in source
    assert "Bundle 13A" in qualification
    assert "RecordEffectScope" not in contracts
    assert "RuntimeTimeMapping" not in source
    assert "Bundle13B" not in qualification
