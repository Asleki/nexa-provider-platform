"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_query_service.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.5 — Audit Query Service
============================================================

Provides deterministic read-only filtering over an AuditRepositoryInterface.
"""
from __future__ import annotations

from .audit_errors import (
    AuditQueryExecutionError,
    AuditQueryServiceConfigurationError,
)
from .audit_query import AuditQuery
from .audit_query_result import AuditQueryResult
from .audit_query_service_interface import AuditQueryServiceInterface
from .audit_record import AuditRecord
from .audit_repository_interface import AuditRepositoryInterface


class AuditQueryService(AuditQueryServiceInterface):
    """Query immutable audit records without mutating repository state."""

    def __init__(self, repository: AuditRepositoryInterface) -> None:
        if not isinstance(repository, AuditRepositoryInterface):
            raise AuditQueryServiceConfigurationError(
                "repository must implement AuditRepositoryInterface."
            )
        self._repository = repository

    @property
    def repository(self) -> AuditRepositoryInterface:
        return self._repository

    def query(self, query: AuditQuery) -> AuditQueryResult:
        if not isinstance(query, AuditQuery):
            raise AuditQueryExecutionError(
                "query must be an AuditQuery value."
            )

        try:
            repository_result = self._repository.list_all()
            records = tuple(
                record
                for record in repository_result.records
                if self._matches(record, query)
            )
            records = tuple(
                sorted(records, key=lambda item: (item.recorded_at, item.audit_id))
            )
            return AuditQueryResult(
                query=query,
                records=records,
                metadata={
                    "repository": self._repository.repository_name,
                    "repository_type": self._repository.repository_type.value,
                    "matched_count": len(records),
                },
            )
        except AuditQueryExecutionError:
            raise
        except Exception as exc:
            raise AuditQueryExecutionError(
                "Audit query could not be executed.",
                metadata={
                    "repository": self._repository.repository_name,
                    "cause": exc.__class__.__name__,
                },
            ) from exc

    @staticmethod
    def _matches(record: AuditRecord, query: AuditQuery) -> bool:
        equality_fields = (
            "audit_id", "action", "outcome", "actor_id", "actor_type",
            "target_namespace", "target_type", "target_id", "runtime_id",
            "runtime_mode", "source", "event_id", "event_type",
            "correlation_id", "causation_id", "request_id", "device_id",
        )
        for name in equality_fields:
            expected = getattr(query, name)
            if expected is not None and getattr(record, name) != expected:
                return False

        if (
            query.recorded_from is not None
            and record.recorded_at < query.recorded_from
        ):
            return False
        if (
            query.recorded_to is not None
            and record.recorded_at > query.recorded_to
        ):
            return False
        return True


__all__ = ["AuditQueryService"]
