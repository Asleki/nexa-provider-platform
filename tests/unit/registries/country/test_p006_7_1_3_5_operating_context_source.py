from pathlib import Path

from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import ApprovalState, RecordEffectScope
from registries.country.operating_context_source import read_bundle13b_source

ROOT = Path(__file__).parents[4]


def test_p006_7_1_3_5_source_reader_reconstructs_validated_bundle13b_authority_snapshot():
    source = read_bundle13b_source(ROOT)
    assert source.realm.realm_id == "realm:nexilabs:novegeo"
    assert source.realm.country_id == "country:novegeo"
    assert {r.runtime_mode for r in source.runtimes} == {
        OperationRuntimeMode.SIMULATION,
        OperationRuntimeMode.PRODUCTION,
    }
    assert set(source.effect_scopes) == set(RecordEffectScope)
    assert set(source.approval_states) == set(ApprovalState)
    assert source.timezone.utc_offset_standard == "+02:00"
    assert source.timezone.dst_observed is False
    assert source.currency.currency_code == "NGC"
    assert source.currency.currency_symbol == "₦G"
