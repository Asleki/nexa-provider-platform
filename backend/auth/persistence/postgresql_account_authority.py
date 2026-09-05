"""P006.UI.10.2 — Read adapter for governed PostgreSQL account persistence.

This module is additive. It does not replace the locked development fixture
service, verify passwords, mint sessions, issue OTPs, approve Developer access,
or provision Enigma secrets. It maps durable PostgreSQL authority records into
existing NexiLabs authentication contracts so later services can compose them.
"""
from __future__ import annotations

from typing import Any

from backend.auth.contracts import IdentityType, Principal

from .contracts import (
    CredentialVerifierRecord,
    DeveloperSetupVerifierRecord,
    EnigmaCatalogueEntryRecord,
    PrimaryEmailRecord,
)


class AccountPersistenceError(RuntimeError):
    """Raised when persisted account authority violates the locked contract."""


class PostgreSQLAccountAuthority:
    """Read-only mapping boundary over the ``nexilabs_auth`` schema."""

    _PRINCIPAL_SQL = """
        SELECT principal_id, username, identity_type
        FROM nexilabs_auth.principal_account
        WHERE username_key = %s
          AND account_state = 'ACTIVE'
        LIMIT 1
    """

    _PERMISSIONS_SQL = """
        SELECT permission_code
        FROM nexilabs_auth.principal_permission
        WHERE principal_id = %s
          AND permission_state = 'ACTIVE'
        ORDER BY permission_code
    """

    _ENIGMA_PROFILE_SQL = """
        SELECT pep.profile_id
        FROM nexilabs_auth.principal_enigma_profile AS pep
        JOIN nexilabs_auth.enigma_profile AS ep
          ON ep.profile_id = pep.profile_id
         AND ep.profile_state = 'ACTIVE'
        WHERE pep.principal_id = %s
          AND pep.assignment_state = 'ACTIVE'
        LIMIT 2
    """

    _PASSWORD_VERIFIER_SQL = """
        SELECT credential_id, principal_id, credential_kind,
               verifier_scheme, verifier_version, verifier_payload
        FROM nexilabs_auth.credential_verifier
        WHERE principal_id = %s
          AND credential_kind = 'password'
          AND credential_state = 'ACTIVE'
        LIMIT 2
    """

    _PRIMARY_EMAIL_SQL = """
        SELECT email_id, principal_id, email_address,
               verification_state, verified_at
        FROM nexilabs_auth.account_email
        WHERE principal_id = %s
          AND is_primary
          AND verification_state <> 'REVOKED'
        LIMIT 2
    """

    _DEVELOPER_SETUP_SQL = """
        SELECT developer_setup_id, request_id, setup_lookup_key,
               setup_secret_verifier_scheme,
               setup_secret_verifier_version,
               setup_secret_verifier_payload,
               setup_state, issued_at, expires_at,
               consumed_at, revoked_at, resulting_principal_id
        FROM nexilabs_auth.developer_setup
        WHERE setup_lookup_key = %s
        LIMIT 1
    """

    _ENIGMA_ENTRY_SQL = """
        SELECT ec.catalogue_id, epc.profile_id, ec.word_length,
               e.day_of_month, e.period, e.word_1, e.word_2, e.word_3
        FROM nexilabs_auth.enigma_profile_catalogue AS epc
        JOIN nexilabs_auth.enigma_profile AS ep
          ON ep.profile_id = epc.profile_id
         AND ep.profile_state = 'ACTIVE'
        JOIN nexilabs_auth.enigma_catalogue AS ec
          ON ec.catalogue_id = epc.catalogue_id
         AND ec.word_length = epc.word_length
         AND ec.catalogue_state = 'ACTIVE'
        JOIN nexilabs_auth.enigma_catalogue_entry AS e
          ON e.catalogue_id = ec.catalogue_id
         AND e.word_length = ec.word_length
        WHERE epc.profile_id = %s
          AND epc.word_length = %s
          AND e.day_of_month = %s
          AND e.period = %s
        LIMIT 1
    """

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=True) is required")
        self.pool = pool

    @staticmethod
    def _username_key(value: object) -> str:
        return str(value).strip().casefold()

    @staticmethod
    def _identity(value: IdentityType | str | None) -> IdentityType | None:
        if value is None or isinstance(value, IdentityType):
            return value
        try:
            return IdentityType(str(value).strip().lower())
        except ValueError as exc:
            raise AccountPersistenceError("unsupported NexiLabs identity type") from exc

    @staticmethod
    def _iso(value: object | None) -> str | None:
        if value is None:
            return None
        isoformat = getattr(value, "isoformat", None)
        return str(isoformat()) if callable(isoformat) else str(value)

    @staticmethod
    def _single(rows: list[tuple[Any, ...]], label: str) -> tuple[Any, ...] | None:
        if len(rows) > 1:
            raise AccountPersistenceError(f"multiple active {label} records")
        return rows[0] if rows else None

    def principal_by_username(
        self,
        username: str,
        *,
        expected_type: IdentityType | str | None = None,
    ) -> Principal | None:
        key = self._username_key(username)
        if not key:
            return None
        expected = self._identity(expected_type)

        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._PRINCIPAL_SQL, (key,))
                row = cursor.fetchone()
                if row is None:
                    return None

                principal_id, canonical_username, identity_value = row
                try:
                    identity_type = IdentityType(str(identity_value))
                except ValueError as exc:
                    raise AccountPersistenceError(
                        "persisted account has unsupported identity type"
                    ) from exc
                if expected is not None and identity_type is not expected:
                    return None

                cursor.execute(self._PERMISSIONS_SQL, (principal_id,))
                permissions = frozenset(str(item[0]) for item in cursor.fetchall())

                enigma_profile_id: str | None = None
                if identity_type is IdentityType.NEXADEVS_DEVELOPER:
                    cursor.execute(self._ENIGMA_PROFILE_SQL, (principal_id,))
                    profile = self._single(list(cursor.fetchall()), "Enigma profile")
                    if profile is None:
                        return None
                    enigma_profile_id = str(profile[0])

        return Principal(
            principal_id=str(principal_id),
            username=str(canonical_username),
            identity_type=identity_type,
            permissions=permissions,
            enigma_profile_id=enigma_profile_id,
        )

    def active_password_verifier(
        self,
        principal_id: str,
    ) -> CredentialVerifierRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._PASSWORD_VERIFIER_SQL, (str(principal_id),))
                row = self._single(list(cursor.fetchall()), "password credential")
        if row is None:
            return None
        return CredentialVerifierRecord(
            credential_id=str(row[0]),
            principal_id=str(row[1]),
            credential_kind=str(row[2]),
            verifier_scheme=str(row[3]),
            verifier_version=int(row[4]),
            verifier_payload=str(row[5]),
        )

    def primary_email(self, principal_id: str) -> PrimaryEmailRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._PRIMARY_EMAIL_SQL, (str(principal_id),))
                row = self._single(list(cursor.fetchall()), "primary email")
        if row is None:
            return None
        return PrimaryEmailRecord(
            email_id=str(row[0]),
            principal_id=str(row[1]),
            email_address=str(row[2]),
            verification_state=str(row[3]),
            verified_at=self._iso(row[4]),
        )

    def developer_setup_by_lookup_key(
        self,
        setup_lookup_key: str,
    ) -> DeveloperSetupVerifierRecord | None:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._DEVELOPER_SETUP_SQL, (str(setup_lookup_key),))
                row = cursor.fetchone()
        if row is None:
            return None
        return DeveloperSetupVerifierRecord(
            developer_setup_id=str(row[0]),
            request_id=str(row[1]),
            setup_lookup_key=str(row[2]),
            verifier_scheme=str(row[3]),
            verifier_version=int(row[4]),
            verifier_payload=str(row[5]),
            setup_state=str(row[6]),
            issued_at=self._iso(row[7]) or "",
            expires_at=self._iso(row[8]) or "",
            consumed_at=self._iso(row[9]),
            revoked_at=self._iso(row[10]),
            resulting_principal_id=str(row[11]) if row[11] is not None else None,
        )

    def enigma_catalogue_entry(
        self,
        *,
        profile_id: str,
        word_length: int,
        day_of_month: int,
        period: str,
    ) -> EnigmaCatalogueEntryRecord | None:
        if int(word_length) not in (3, 4, 5):
            raise ValueError("word_length must be 3, 4 or 5")
        if int(day_of_month) not in range(1, 32):
            raise ValueError("day_of_month must be between 1 and 31")
        normalized_period = str(period).strip().title()
        if normalized_period not in {"Morning", "Noon", "Evening"}:
            raise ValueError("period must be Morning, Noon or Evening")

        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    self._ENIGMA_ENTRY_SQL,
                    (
                        str(profile_id),
                        int(word_length),
                        int(day_of_month),
                        normalized_period,
                    ),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return EnigmaCatalogueEntryRecord(
            catalogue_id=str(row[0]),
            profile_id=str(row[1]),
            word_length=int(row[2]),
            day_of_month=int(row[3]),
            period=str(row[4]),
            words=(str(row[5]), str(row[6]), str(row[7])),
        )


__all__ = ["AccountPersistenceError", "PostgreSQLAccountAuthority"]
