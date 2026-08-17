import pytest
from registries.nngla.spatial_fabric.bundle17n import RuntimeCommand,RuntimePrincipal,RuntimeCommandDispatcher
from registries.nngla.spatial_fabric.bundle17n.idempotency import CommandIdempotencyConflict
def make(payload,key="same"):
    return RuntimeCommand("ALLOCATE_ADDRESS",1,"production","RUNTIME_SCOPED","op",key,"corr",payload)
def test_same_semantics_replay_and_different_semantics_conflict():
    d=RuntimeCommandDispatcher()
    d.register_handler("address.allocate",lambda c:{"references":{"address_id":"NG-ADR-000999"}})
    p=RuntimePrincipal("op","production",frozenset({"nngla.allocate_address"}))
    c=make({"site_id":"site:1","address_series_id":"series:1"})
    first=d.execute(c,p,approval_granted=True); second=d.execute(c,p,approval_granted=True)
    assert first.receipt_id==second.receipt_id and second.replayed
    changed=make({"site_id":"site:2","address_series_id":"series:1"})
    with pytest.raises(CommandIdempotencyConflict): d.execute(changed,p,approval_granted=True)
