from contextlib import nullcontext
import pytest
from registries.nngla.spatial_fabric.bundle17n import RuntimeCommand,RuntimePrincipal,RuntimeCommandDispatcher
from registries.nngla.spatial_fabric.bundle17n.bulk import RuntimeBulkExecutor
def commands():
    return tuple(RuntimeCommand("ALLOCATE_ADDRESS",1,"production","RUNTIME_SCOPED","op",f"i:{n}","corr",{"site_id":f"site:{n}","address_series_id":"series"}) for n in range(3))
def test_atomic_bulk_requires_transaction_boundary_and_executes_with_one():
    d=RuntimeCommandDispatcher(); d.register_handler("address.allocate",lambda c:{"references":{"address_id":c.payload["site_id"]}})
    p=RuntimePrincipal("op","production",frozenset({"nngla.allocate_address"}))
    with pytest.raises(RuntimeError): RuntimeBulkExecutor(d).execute(commands(),p,policy_code="BULK_ATOMIC",approval_granted=True)
    result=RuntimeBulkExecutor(d,transaction_factory=nullcontext).execute(commands(),p,policy_code="BULK_ATOMIC",approval_granted=True)
    assert len(result.receipts)==3 and result.failure_count==0
def test_preview_does_not_execute_handlers():
    d=RuntimeCommandDispatcher(); called=[]
    d.register_handler("address.allocate",lambda c:called.append(c) or {})
    p=RuntimePrincipal("op","production",frozenset({"nngla.allocate_address"}))
    r=RuntimeBulkExecutor(d).execute(commands(),p,policy_code="BULK_PREVIEW",approval_granted=True)
    assert r.preview_only and called==[]
