"""P006.UI.10.2.C — read-only PostgreSQL Admin Operator/review authority adapter.

This adapter reads durable authority only. It does not authenticate passwords,
mint sessions/elevations, approve requests, bootstrap an Admin, or mutate rows.
"""
from __future__ import annotations

from typing import Any

from backend.auth.persistence.contracts import CredentialVerifierRecord

from .contracts import (
    ADMIN_PASSWORD_KIND,
    AdminOperatorRecord,
    AdminReviewPersistenceError,
    DeveloperAccessDecisionRecord,
)


class PostgreSQLAdminReviewAuthority:
    """Read-only mapping boundary over P006.UI.10.2.C authority."""

    _ACTIVE_OPERATOR_BY_PRINCIPAL_SQL = """
        SELECT ao.admin_operator_id, ao.principal_id, ao.admin_developer_id,
               ao.bound_admin_email_id, e.email_address, ao.admin_state,
               ao.created_at, ao.disabled_at, ao.bootstrap_reference,
               ao.audit_reference
        FROM nexilabs_auth.admin_operator AS ao
        JOIN nexilabs_auth.principal_account AS p
          ON p.principal_id = ao.principal_id
         AND p.identity_type = 'nexadevs_developer'
         AND p.account_state = 'ACTIVE'
        JOIN nexilabs_auth.account_email AS e
          ON e.email_id = ao.bound_admin_email_id
         AND e.principal_id = ao.principal_id
         AND e.verification_state = 'VERIFIED'
        WHERE ao.principal_id = %s
          AND ao.admin_state = 'ACTIVE'
        LIMIT 2
    """

    _ACTIVE_OPERATOR_BY_DEVELOPER_ID_SQL = """
        SELECT ao.admin_operator_id, ao.principal_id, ao.admin_developer_id,
               ao.bound_admin_email_id, e.email_address, ao.admin_state,
               ao.created_at, ao.disabled_at, ao.bootstrap_reference,
               ao.audit_reference
        FROM nexilabs_auth.admin_operator AS ao
        JOIN nexilabs_auth.principal_account AS p
          ON p.principal_id = ao.principal_id
         AND p.identity_type = 'nexadevs_developer'
         AND p.account_state = 'ACTIVE'
        JOIN nexilabs_auth.account_email AS e
          ON e.email_id = ao.bound_admin_email_id
         AND e.principal_id = ao.principal_id
         AND e.verification_state = 'VERIFIED'
        WHERE ao.admin_developer_id_key = lower(btrim(%s))
          AND ao.admin_state = 'ACTIVE'
        LIMIT 2
    """

    _ADMIN_PASSWORD_SQL = """
        SELECT credential_id, principal_id, credential_kind,
               verifier_scheme, verifier_version, verifier_payload
        FROM nexilabs_auth.credential_verifier
        WHERE principal_id = %s
          AND credential_kind = 'ADMIN_PASSWORD'
          AND credential_state = 'ACTIVE'
        LIMIT 2
    """

    _DEVELOPER_DECISION_SQL = """
        SELECT decision_id, request_id, reviewer_principal_id,
               admin_operator_id, decision, reason_code, safe_explanation,
               internal_reference, policy_version, receipt_reference, decided_at
        FROM nexilabs_auth.developer_access_decision
        WHERE request_id = %s
        LIMIT 2
    """

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=True) is required")
        self.pool = pool

    @staticmethod
    def _iso(value: object | None) -> str | None:
        if value is None:
            return None
        isoformat = getattr(value, "isoformat", None)
        return str(isoformat()) if callable(isoformat) else str(value)

    @staticmethod
    def _single(rows: list[tuple[Any, ...]], label: str) -> tuple[Any, ...] | None:
        if len(rows) > 1:
            raise AdminReviewPersistenceError(f"multiple active {label} records")
        return rows[0] if rows else None

    @classmethod
    def _operator_record(cls, row: tuple[Any, ...] | None) -> AdminOperatorRecord | None:
        if row is None:
            return None
        return AdminOperatorRecord(
            admin_operator_id=str(row[0]),
            principal_id=str(row[1]),
            admin_developer_id=str(row[2]),
            bound_admin_email_id=str(row[3]),
            bound_admin_email=str(row[4]),
            admin_state=str(row[5]),
            created_at=cls._iso(row[6]) or "",
            disabled_at=cls._iso(row[7]),
            bootstrap_reference=str(row[8]) if row[8] is not None else None,
            audit_reference=str(row[9]),
        )

    def active_admin_operator(self, principal_id: str) -> AdminOperatorRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ACTIVE_OPERATOR_BY_PRINCIPAL_SQL, (str(principal_id),))
                row = self._single(list(cursor.fetchall()), "Admin Operator")
        return self._operator_record(row)

    def active_admin_operator_by_developer_id(
        self, admin_developer_id: str
    ) -> AdminOperatorRecord | None:
        value = str(admin_developer_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ACTIVE_OPERATOR_BY_DEVELOPER_ID_SQL, (value,))
                row = self._single(list(cursor.fetchall()), "Admin Developer identifier")
        return self._operator_record(row)

    def active_admin_password_verifier(
        self, principal_id: str
    ) -> CredentialVerifierRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ADMIN_PASSWORD_SQL, (str(principal_id),))
                row = self._single(list(cursor.fetchall()), "ADMIN_PASSWORD credential")
        if row is None:
            return None
        record = CredentialVerifierRecord(
            credential_id=str(row[0]),
            principal_id=str(row[1]),
            credential_kind=str(row[2]),
            verifier_scheme=str(row[3]),
            verifier_version=int(row[4]),
            verifier_payload=str(row[5]),
        )
        if record.credential_kind != ADMIN_PASSWORD_KIND:
            raise AdminReviewPersistenceError("Admin password read returned the wrong credential kind")
        return record

    def developer_access_decision(
        self, request_id: str
    ) -> DeveloperAccessDecisionRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._DEVELOPER_DECISION_SQL, (str(request_id),))
                row = self._single(list(cursor.fetchall()), "Developer access decision")
        if row is None:
            return None
        return DeveloperAccessDecisionRecord(
            decision_id=str(row[0]),
            request_id=str(row[1]),
            reviewer_principal_id=str(row[2]),
            admin_operator_id=str(row[3]),
            decision=str(row[4]),
            reason_code=str(row[5]) if row[5] is not None else None,
            safe_explanation=str(row[6]) if row[6] is not None else None,
            internal_reference=str(row[7]),
            policy_version=str(row[8]),
            receipt_reference=str(row[9]),
            decided_at=self._iso(row[10]) or "",
        )


__all__ = ["PostgreSQLAdminReviewAuthority"]
