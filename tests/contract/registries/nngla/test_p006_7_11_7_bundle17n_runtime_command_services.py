import pytest
from registries.nngla.spatial_fabric.bundle17n import RuntimeCommand,RuntimePrincipal,RuntimeCommandDispatcher,bundle17n_is_qualified
from registries.nngla.spatial_fabric.bundle17n.dispatcher import CommandRejected

def test_p006_7_11_7_18_runtime_commands_are_csv_optional_and_runtime_bounded():
    assert bundle17n_is_qualified()
    simulation=RuntimePrincipal("service:nexilabs","simulation",frozenset({"nngla.create_addressable_site","nngla.allocate_address"}))
    dispatcher=RuntimeCommandDispatcher()
    dispatcher.register_handler("address.create_site",lambda c:{"references":{"site_id":"site:nngla:simulation-demo"}})
    site=RuntimeCommand("CREATE_ADDRESSABLE_SITE",1,"simulation","RUNTIME_SCOPED",simulation.principal_id,"event:site","corr:world",{"source_reference":"nexilabs:event:1"})
    receipt=dispatcher.execute(site,simulation,approval_granted=True)
    assert dict(receipt.references)["site_id"].startswith("site:nngla:")
    # Locked Bundle 17H says Simulation may form/propose sites but may not consume sovereign NG-ADR identities/numbers.
    forbidden=RuntimeCommand("ALLOCATE_ADDRESS",1,"simulation","RUNTIME_SCOPED",simulation.principal_id,"event:address","corr:world",{"site_id":"site:nngla:simulation-demo","address_series_id":"series:sim"})
    with pytest.raises(CommandRejected) as exc:
        dispatcher.execute(forbidden,simulation,approval_granted=True)
    assert "COMMAND_RUNTIME_NOT_ALLOWED" in exc.value.reasons
