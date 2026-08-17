import pytest
from registries.nngla.spatial_fabric.bundle17n import RuntimeCommand,RuntimePrincipal,RuntimeCommandDispatcher
from registries.nngla.spatial_fabric.bundle17n.dispatcher import CommandRejected
def test_dispatcher_requires_registered_domain_handler_and_propagates_trace_refs():
    p=RuntimePrincipal("op","production",frozenset({"nngla.reserve_parcel_reference"}))
    c=RuntimeCommand("RESERVE_PARCEL_REFERENCE",1,"production","RUNTIME_SCOPED","op","i","corr",{"cadastral_series_id":"series:1"})
    d=RuntimeCommandDispatcher()
    with pytest.raises(CommandRejected): d.execute(c,p,approval_granted=True)
    d.register_handler("parcel.reserve_reference",lambda cmd:{"references":{"parcel_reference":"NV-01-001-0001"},"event_id":"e:1","audit_id":"a:1"})
    r=d.execute(c,p,approval_granted=True)
    assert dict(r.references)["parcel_reference"]=="NV-01-001-0001"
    assert r.event_id=="e:1" and r.audit_id=="a:1"
