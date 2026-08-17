from datetime import datetime, timezone
import pytest
from registries.nngla.spatial_fabric.bundle17n.contracts import RuntimeCommand, RuntimePrincipal

def test_runtime_command_and_principal_normalize_runtime():
    p=RuntimePrincipal("operator:1","SIMULATION",frozenset({"x"}))
    c=RuntimeCommand("ALLOCATE_ADDRESS",1,"simulation","RUNTIME_SCOPED","operator:1","idem:1","corr:1",{"site_id":"site:1"},requested_at=datetime.now(timezone.utc))
    assert p.runtime_mode.value=="simulation" and c.runtime_mode.value=="simulation"
    with pytest.raises(ValueError):
        RuntimeCommand("",1,"simulation","RUNTIME_SCOPED","p","i","c",{})
