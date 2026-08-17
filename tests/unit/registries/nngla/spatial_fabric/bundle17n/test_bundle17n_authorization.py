from registries.nngla.spatial_fabric.bundle17n.contracts import RuntimeCommand,RuntimePrincipal
from registries.nngla.spatial_fabric.bundle17n.authorization import authorize
def cmd(principal="operator:1",effect="RUNTIME_SCOPED",runtime="production"):
    return RuntimeCommand("ALLOCATE_ADDRESS",1,runtime,effect,principal,"idem","corr",{"site_id":"s","address_series_id":"a"})
def test_authorization_is_foundation_command_and_principal_intersection():
    p=RuntimePrincipal("operator:1","production",frozenset({"nngla.allocate_address"}))
    assert authorize(cmd(),p,approval_granted=True).allowed
    assert "APPROVAL_REQUIRED" in authorize(cmd(),p).reasons
    wrong=RuntimePrincipal("operator:1","simulation",p.permissions)
    sim=cmd(runtime="simulation")
    assert "COMMAND_RUNTIME_NOT_ALLOWED" in authorize(sim,wrong,approval_granted=True).reasons
    assert "EFFECT_SCOPE_NOT_AUTHORIZED" in authorize(cmd(effect="SHARED_REFERENCE"),p,approval_granted=True).reasons
