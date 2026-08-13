from registries.nngla.source import load_authority
from registries.nngla.authority import AuthorityRoleCode

def test_nngla_authority_identity_and_roles():
    authority, roles = load_authority()
    assert authority.authority_id == "authority:nngla"
    assert authority.country_record_id == "country:novegeo"
    assert authority.world_realm_id == "realm:nexilabs:novegeo"
    assert len(roles) == 10
    assert {r.role_code for r in roles} == set(AuthorityRoleCode)

def test_nngla_roles_remain_one_authority_with_capabilities():
    _, roles = load_authority()
    assert {r.authority_id for r in roles} == {"authority:nngla"}
    road = next(r for r in roles if r.role_code is AuthorityRoleCode.ROAD_ADDRESS_REFERENCE)
    assert road.may_create and road.may_review and road.may_approve and road.may_gazette and road.may_retire
