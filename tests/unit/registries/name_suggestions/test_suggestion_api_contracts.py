from datetime import datetime, timezone
from types import MappingProxyType
import pytest
from registries.name_suggestions.suggestion_api_operation import SuggestionApiOperation
from registries.name_suggestions.suggestion_api_request import SuggestionApiRequest
from registries.name_suggestions.suggestion_api_response import SuggestionApiResponse
from registries.name_suggestions.suggestion_api_errors import SuggestionApiResultError, SuggestionApiValidationError

NOW = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)


def test_request_is_immutable_normalized_and_serializable():
    request = SuggestionApiRequest(" req-1 ", "suggest_single", NOW, " Simulation ", {"name_kind": "first_name"}, {"trace": "x"})
    assert request.request_id == "req-1"
    assert request.operation is SuggestionApiOperation.SUGGEST_SINGLE
    assert request.runtime_mode == "simulation"
    assert isinstance(request.payload, MappingProxyType)
    assert request.to_dict()["requested_at"].endswith("+00:00")


def test_request_rejects_naive_time_and_mutable_non_mapping_payload():
    with pytest.raises(SuggestionApiValidationError):
        SuggestionApiRequest("req", "normalize", datetime(2026, 1, 1), payload={})
    with pytest.raises(SuggestionApiValidationError):
        SuggestionApiRequest("req", "normalize", NOW, payload=[])


def test_response_enforces_success_failure_shape():
    success = SuggestionApiResponse.succeeded(request_id="req", operation="normalize", completed_at=NOW, data={"x": 1})
    failure = SuggestionApiResponse.failed(request_id="req", operation="normalize", completed_at=NOW, error={"message": "bad"})
    assert success.success and success.error is None
    assert not failure.success and failure.data is None
    with pytest.raises(SuggestionApiResultError):
        SuggestionApiResponse("req", "normalize", NOW, True, data={}, error={"message": "bad"})
