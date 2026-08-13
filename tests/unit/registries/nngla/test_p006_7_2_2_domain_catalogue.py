from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import RecordEffectScope
from registries.nngla.domain_catalogue import NNGLARecordFamily
from registries.nngla.source import load_domain_catalogue

def test_catalogue_contains_nine_governed_families_and_both_runtimes():
    cat = load_domain_catalogue()
    assert cat.families == frozenset(NNGLARecordFamily)
    for family in NNGLARecordFamily:
        assert cat.rule_for(family, OperationRuntimeMode.SIMULATION)
        assert cat.rule_for(family, OperationRuntimeMode.PRODUCTION)

def test_runtime_and_effect_scope_remain_distinct():
    cat = load_domain_catalogue()
    sim_geom = cat.rule_for(NNGLARecordFamily.GEOMETRY, OperationRuntimeMode.SIMULATION)
    prod_geom = cat.rule_for(NNGLARecordFamily.GEOMETRY, OperationRuntimeMode.PRODUCTION)
    assert sim_geom.effect_scope is RecordEffectScope.SHARED_REFERENCE
    assert prod_geom.effect_scope is RecordEffectScope.SHARED_REFERENCE
    assert sim_geom.approval_required and prod_geom.approval_required
