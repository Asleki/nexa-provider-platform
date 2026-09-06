"""P006.UI.10.2.D — read-only PostgreSQL email-verification challenge authority.

This adapter exposes durable challenge records only. It does not generate OTPs,
compare user-entered codes, send mail, increment attempts/resends, transition
challenge state, verify account_email rows, activate principals, or mint sessions.
"""
from __future__ import annotations

from typing import Any

from .contracts import EmailVerificationChallengeRecord, EmailVerificationPersistenceError


class PostgreSQLEmailVerificationAuthority:
    """Read-only mapping boundary over the D challenge authority."""

    _COLUMNS = """
        c.challenge_id, c.principal_id, c.email_id,
        c.otp_verifier_scheme, c.otp_verifier_version, c.otp_verifier_payload,
        c.challenge_state, c.policy_version,
        c.issued_at, c.expires_at, c.consumed_at, c.invalidated_at,
        c.attempt_count, c.max_attempts, c.resend_count, c.last_resend_at
    """

    _CHALLENGE_BY_ID_SQL = f"""
        SELECT {_COLUMNS}
        FROM nexilabs_auth.email_verification_challenge AS c
        WHERE c.challenge_id = %s
        LIMIT 1
    """

    _ISSUED_CHALLENGE_SQL = f"""
        SELECT {_COLUMNS}
        FROM nexilabs_auth.email_verification_challenge AS c
        JOIN nexilabs_auth.account_email AS e
          ON e.email_id = c.email_id
         AND e.principal_id = c.principal_id
         AND e.verification_state <> 'REVOKED'
        WHERE c.principal_id = %s
          AND c.email_id = %s
          AND c.challenge_state = 'ISSUED'
        ORDER BY c.issued_at DESC
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

    @classmethod
    def _record(cls, row: tuple[Any, ...] | None) -> EmailVerificationChallengeRecord | None:
        if row is None:
            return None
        return EmailVerificationChallengeRecord(
            challenge_id=str(row[0]),
            principal_id=str(row[1]),
            email_id=str(row[2]),
            otp_verifier_scheme=str(row[3]),
            otp_verifier_version=int(row[4]),
            otp_verifier_payload=str(row[5]),
            challenge_state=str(row[6]),
            policy_version=str(row[7]),
            issued_at=cls._iso(row[8]) or "",
            expires_at=cls._iso(row[9]) or "",
            consumed_at=cls._iso(row[10]),
            invalidated_at=cls._iso(row[11]),
            attempt_count=int(row[12]),
            max_attempts=int(row[13]),
            resend_count=int(row[14]),
            last_resend_at=cls._iso(row[15]),
        )

    @staticmethod
    def _single(rows: list[tuple[Any, ...]], label: str) -> tuple[Any, ...] | None:
        if len(rows) > 1:
            raise EmailVerificationPersistenceError(f"multiple {label} records")
        return rows[0] if rows else None

    def challenge_by_id(self, challenge_id: str) -> EmailVerificationChallengeRecord | None:
        value = str(challenge_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._CHALLENGE_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._record(row)

    def issued_challenge(
        self,
        *,
        principal_id: str,
        email_id: str,
    ) -> EmailVerificationChallengeRecord | None:
        principal = str(principal_id).strip()
        email = str(email_id).strip()
        if not principal or not email:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ISSUED_CHALLENGE_SQL, (principal, email))
                row = self._single(list(cursor.fetchall()), "ISSUED email challenge")
        return self._record(row)


__all__ = ["PostgreSQLEmailVerificationAuthority"]
