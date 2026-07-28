from datetime import datetime, timezone

from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest
from registries.audit import RegistryAuditResult
from registries.ports import RegistryAuditPort

NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


class FailingAuditPort(RegistryAuditPort):
    def record(self, *, request, response):
        return RegistryAuditResult.failed(
            error_code="NPP-REGISTRY-AUDIT-030",
            error_type="AuditUnavailable",
            message="Registry audit could not be recorded.",
        )


def test_successful_registry_operation_remains_successful_when_audit_fails() -> None:
    api = RegistryApi(
        MemoryRegistryRepository(),
        clock=lambda: NOW,
        audit_port=FailingAuditPort(),
    )
    request = RegistryApiRequest(
        request_id="req-count",
        operation="count",
        requested_at=NOW,
    )

    response = api.handle(request)

    assert response.success is True
    assert response.data["repository_result"]["metadata"]["count"] == 0
    assert response.metadata["audit_attempted"] is True
    assert response.metadata["audit_success"] is False
    assert response.metadata["audit_requires_attention"] is True
