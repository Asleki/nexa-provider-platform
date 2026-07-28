from datetime import datetime, timezone
import pytest
from registries.api import RegistryApiResponse, RegistryApiResultError

def test_response_factories_enforce_success_failure_shape():
    ok=RegistryApiResponse.succeeded(request_id="r",operation="count",completed_at=datetime.now(timezone.utc),data={"count":1})
    assert ok.success and ok.to_dict()["data"]=={"count":1}
    bad=RegistryApiResponse.failed(request_id="r",operation="count",completed_at=datetime.now(timezone.utc),error={"type":"X"})
    assert not bad.success
    with pytest.raises(RegistryApiResultError):
        RegistryApiResponse("r","count",datetime.now(timezone.utc),False,data={})
