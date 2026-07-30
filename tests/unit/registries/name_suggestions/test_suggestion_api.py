from datetime import datetime, timezone
import pytest
from registries.name_suggestions.full_name_composition import FullNameComposition
from registries.name_suggestions.suggestion_api import SuggestionApi
from registries.name_suggestions.suggestion_api_request import SuggestionApiRequest
from registries.names import FirstName, MiddleName, Surname, MemoryNameRepository, NameMetadata

NOW = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)


def _repo():
    repo = MemoryNameRepository()
    repo.add(FirstName("name:first:a", "Amina").as_canonical())
    repo.add(FirstName("name:first:b", "Binta").as_canonical())
    repo.add(MiddleName("name:middle:r", "Rudo").as_canonical())
    repo.add(Surname("name:surname:n", "Ncube").as_canonical())
    repo.add(FirstName("name:first:p", "Prod", NameMetadata(runtime_mode="production")).as_canonical())
    return repo


def _request(operation, payload=None, runtime="simulation"):
    return SuggestionApiRequest("req-1", operation, NOW, runtime, {} if payload is None else payload, {"trace_id": "t-1"})


def test_normalize_and_duplicate_check_operations_return_stable_envelopes():
    api = SuggestionApi(_repo(), clock=lambda: NOW)
    normalized = api.execute(_request("normalize", {"value": "  AMINA  "}))
    assert normalized.success and normalized.data["comparison_value"] == "amina"
    duplicate = api.execute(_request("check_duplicate", {
        "canonical_name_id": "name:first:a",
        "excluded_values": [" amina "],
    }))
    assert duplicate.success and duplicate.data["duplicate"] is True


def test_single_pair_trio_and_full_name_operations_reuse_locked_services():
    api = SuggestionApi(_repo(), clock=lambda: NOW)
    single = api.execute(_request("suggest_single", {"name_kind": "first_name"}))
    pair = api.execute(_request("suggest_pair"))
    trio = api.execute(_request("suggest_trio"))
    full = api.execute(_request("suggest_full_name", {"composition": FullNameComposition.FIRST_SURNAME.value}))
    assert single.data["rendered_value"] == "Amina"
    assert pair.data["rendered_value"] == "Amina Ncube"
    assert trio.data["rendered_value"] == "Amina Rudo Ncube"
    assert full.data["composition"] == "first_surname"


def test_exclusions_select_next_candidate_without_mutating_repository():
    repo = _repo(); before = repo.count()
    response = SuggestionApi(repo, clock=lambda: NOW).execute(_request("suggest_single", {
        "name_kind": "first_name",
        "excluded_values": ["AMINA"],
    }))
    assert response.success and response.data["rendered_value"] == "Binta"
    assert repo.count() == before


def test_runtime_mode_isolated_and_failures_are_returned_not_raised():
    api = SuggestionApi(_repo(), clock=lambda: NOW)
    production = api.execute(_request("suggest_single", {"name_kind": "first_name"}, "production"))
    missing = api.execute(_request("suggest_single", {"name_kind": "surname"}, "production"))
    invalid = api.execute(_request("normalize", {}))
    assert production.success and production.data["rendered_value"] == "Prod"
    assert not missing.success and missing.error["type"] == "NameSuggestionCandidateNotFoundError"
    assert not invalid.success and invalid.error["category"] == "validation"


def test_execute_rejects_wrong_request_type_at_contract_boundary():
    with pytest.raises(TypeError):
        SuggestionApi(_repo()).execute({})
