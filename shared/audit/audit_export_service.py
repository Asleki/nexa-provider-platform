"""
Nexa Provider Platform
File: shared/audit/audit_export_service.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.7 — Audit Export
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .audit_errors import (
    AuditExportExecutionError,
    AuditExportValidationError,
)
from .audit_export_request import AuditExportRequest
from .audit_export_result import AuditExportResult
from .audit_export_service_interface import AuditExportServiceInterface
from .audit_query import AuditQuery
from .audit_record import AuditRecord


class AuditExportService(AuditExportServiceInterface):
    """Pure read-only transformer for immutable audit query results."""

    SCHEMA_VERSION = 1

    @staticmethod
    def _serialize_datetime(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    @classmethod
    def _serialize_query(cls, query: AuditQuery) -> dict[str, Any]:
        return {
            "audit_id": query.audit_id,
            "action": query.action.value if query.action is not None else None,
            "outcome": (
                query.outcome.value if query.outcome is not None else None
            ),
            "actor_id": query.actor_id,
            "actor_type": query.actor_type,
            "target_namespace": query.target_namespace,
            "target_type": query.target_type,
            "target_id": query.target_id,
            "runtime_id": query.runtime_id,
            "runtime_mode": query.runtime_mode,
            "source": query.source,
            "event_id": query.event_id,
            "event_type": query.event_type,
            "correlation_id": query.correlation_id,
            "causation_id": query.causation_id,
            "request_id": query.request_id,
            "device_id": query.device_id,
            "recorded_from": cls._serialize_datetime(query.recorded_from),
            "recorded_to": cls._serialize_datetime(query.recorded_to),
        }

    @staticmethod
    def _serialize_record(record: AuditRecord) -> dict[str, Any]:
        return record.to_dict()

    def export(self, request: AuditExportRequest) -> AuditExportResult:
        if not isinstance(request, AuditExportRequest):
            raise AuditExportValidationError(
                "request must be an AuditExportRequest."
            )
        try:
            query_result = request.query_result
            return AuditExportResult(
                export_id=request.export_id,
                generated_at=request.generated_at,
                schema_version=self.SCHEMA_VERSION,
                records=tuple(
                    self._serialize_record(record)
                    for record in query_result.records
                ),
                query=self._serialize_query(query_result.query),
                query_metadata=query_result.metadata,
                metadata=request.metadata,
            )
        except AuditExportValidationError:
            raise
        except Exception as exc:
            raise AuditExportExecutionError(
                "Audit export generation failed."
            ) from exc


__all__ = ["AuditExportService"]
