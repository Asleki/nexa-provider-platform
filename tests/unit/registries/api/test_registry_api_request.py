from datetime import datetime, timezone
import pytest
from registries.api import RegistryApiRequest, RegistryApiValidationError

def test_request_is_immutable_normalized_and_serializable():
    payload={"registry_id":"x"}
    req=RegistryApiRequest(" req-1 ","get",datetime.now(timezone.utc),payload,{"mode":"simulation"})
    payload["registry_id"]="changed"
    assert req.request_id=="req-1" and req.payload["registry_id"]=="x"
    assert req.to_dict()["operation"]=="get"
    with pytest.raises(TypeError): req.payload["x"]=1

def test_request_requires_aware_time():
    with pytest.raises(RegistryApiValidationError):
        RegistryApiRequest("x","get",datetime.now())
