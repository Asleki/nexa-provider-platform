from datetime import datetime, timezone
import pytest

from shared.audit.audit_errors import AuditExportResultError
from shared.audit.audit_export_result import AuditExportResult


def test_result_is_immutable_and_detached() -> None:
    source = {"audit_id": "A-1", "metadata": {"safe": True}}
    result = AuditExportResult(
        export_id="EXP-1",
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        schema_version=1,
        records=(source,),
        query={"actor_id": "actor-1"},
    )
    source["audit_id"] = "changed"
    assert result.records[0]["audit_id"] == "A-1"
    assert result.count == 1
    assert not result.empty
    with pytest.raises(TypeError):
        result.records[0]["audit_id"] = "changed"

    detached = result.to_dict()
    detached["records"][0]["audit_id"] = "detached-change"
    assert result.records[0]["audit_id"] == "A-1"


def test_empty_result_properties() -> None:
    result = AuditExportResult(
        export_id="EXP-EMPTY",
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        schema_version=1,
    )
    assert result.count == 0
    assert result.empty
    assert result.to_dict()["record_count"] == 0


@pytest.mark.parametrize("schema_version", [0, -1, True, "1"])
def test_result_rejects_invalid_schema_version(schema_version) -> None:
    with pytest.raises(AuditExportResultError):
        AuditExportResult(
            export_id="EXP-1",
            generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            schema_version=schema_version,
        )
