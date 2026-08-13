from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.nngla.authority import AuthorityRoleCode
from registries.nngla.domain_catalogue import NNGLARecordFamily
from registries.nngla.source import load_authority, load_domain_catalogue, load_identifier_catalogue, load_lifecycle_definitions

def test_bundle14a_source_contract_is_complete_and_cross_linked():
    authority, roles = load_authority()
    domains = load_domain_catalogue()
    ids = load_identifier_catalogue()
    lifecycle = load_lifecycle_definitions()
    assert authority.authority_code == "NNGLA"
    assert len(roles) == len(AuthorityRoleCode) == 10
    assert len(domains.families) == len(NNGLARecordFamily) == 9
    assert len(ids.namespaces) == 11 and len(ids.formats) == 28
    assert len(lifecycle) == 20
    assert {n.issuing_authority_code for n in ids.namespaces} == {"NNGLA"}
    assert {f.issuing_authority_code for f in ids.formats} == {"NNGLA"}

def test_bundle14a_preserves_runtime_independent_identity_and_runtime_aware_domain_rules():
    domains = load_domain_catalogue()
    ids = load_identifier_catalogue()
    assert all(not f.runtime_scoped for f in ids.formats)
    for family in NNGLARecordFamily:
        assert domains.rule_for(family, OperationRuntimeMode.SIMULATION)
        assert domains.rule_for(family, OperationRuntimeMode.PRODUCTION)
