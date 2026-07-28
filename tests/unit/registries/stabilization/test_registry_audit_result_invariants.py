from datetime import datetime, timezone

import pytest

from registries.audit import RegistryAuditResult, RegistryAuditResultError
from shared.audit import AuditAction, AuditOutcome, AuditRecord, AuditRepositoryResult

NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def repository_result() -> AuditRepositoryResult:
    record = AuditRecord(
        audit_id="AUD-1",
        version=1,
        recorded_at=NOW,
        actor_id="system",
        actor_type="system",
        action=AuditAction.READ,
        target_namespace="registries",
        target_type="registry_catalogue",
        target_id="master-registry",
        outcome=AuditOutcome.SUCCESS,
        runtime_id="registry-runtime",
        runtime_mode="simulation",
        source="registry_api",
        correlation_id="req-1",
    )
    return AuditRepositoryResult.appended(repository="memory-audit", record=record)


def test_recorded_result_is_internally_consistent() -> None:
    result = RegistryAuditResult.recorded(
        repository_result(), event_id="evt-1", event_type="registry.registered"
    )

    assert result.attempted is True
    assert result.success is True
    assert result.audit_id == "AUD-1"
    assert result.repository_result is not None
    assert result.error_code is None
    assert result.to_metadata()["audit_event_type"] == "registry.registered"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"repository_result": repository_result(), "message": "recorded", "error_code": "X", "error_type": "Boom"},
        {"audit_id": "AUD-1", "message": "recorded"},
        {"repository_result": repository_result(), "message": ""},
    ],
)
def test_successful_result_rejects_contradictory_state(kwargs) -> None:
    with pytest.raises(RegistryAuditResultError):
        RegistryAuditResult(attempted=True, success=True, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"message": "failed"},
        {"error_code": "X", "message": "failed"},
        {"error_type": "Boom", "message": "failed"},
        {"error_code": "X", "error_type": "Boom", "message": ""},
        {"audit_id": "AUD-1", "error_code": "X", "error_type": "Boom", "message": "failed"},
        {"repository_result": repository_result(), "error_code": "X", "error_type": "Boom", "message": "failed"},
    ],
)
def test_failed_result_requires_actionable_failure_state(kwargs) -> None:
    with pytest.raises(RegistryAuditResultError):
        RegistryAuditResult(attempted=True, success=False, **kwargs)


def test_unattempted_result_cannot_claim_execution_details() -> None:
    clean = RegistryAuditResult(attempted=False, success=False)
    assert clean.to_metadata() == {"audit_attempted": False, "audit_success": False}

    with pytest.raises(RegistryAuditResultError):
        RegistryAuditResult(
            attempted=False,
            success=False,
            error_code="X",
            error_type="Boom",
            message="not attempted",
        )


def test_text_fields_are_normalised_and_metadata_is_top_level_immutable() -> None:
    source = {"reason": "repository unavailable"}
    result = RegistryAuditResult.failed(
        error_code=" X ",
        error_type=" Boom ",
        message=" failed ",
        metadata=source,
    )
    source["reason"] = "changed"

    assert result.error_code == "X"
    assert result.error_type == "Boom"
    assert result.message == "failed"
    assert result.metadata["reason"] == "repository unavailable"
    with pytest.raises(TypeError):
        result.metadata["new"] = "value"
