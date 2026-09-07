"""P006.UI.10.2.E — read-only PostgreSQL bundle/storage/delivery authority.

This adapter exposes durable authority only. It does not generate Enigma material,
create archives, store object bytes, call S3/KMS, mint/compare delivery tokens,
change lifecycle state, increment download counters, send mail or activate accounts.
"""
from __future__ import annotations

from typing import Any

from .contracts import (
    CredentialBundlePersistenceError,
    CredentialBundleRecord,
    CredentialBundleSecretRecord,
    CredentialDeliveryRecord,
)


class PostgreSQLCredentialBundleAuthority:
    """Read-only mapping boundary over the P006.UI.10.2.E authority."""

    _BUNDLE_COLUMNS = """
        b.bundle_id, b.principal_id, b.enigma_profile_id, b.bundle_state,
        b.object_provider_code, b.object_key, b.content_sha256, b.byte_size,
        b.created_at, b.integrity_verified_at, b.object_confirmed_at, b.ready_at,
        b.expires_at, b.retention_until, b.invalidated_at, b.retired_at
    """
    _DELIVERY_COLUMNS = """
        d.delivery_id, d.bundle_id,
        d.token_verifier_scheme, d.token_verifier_version, d.token_verifier_payload,
        d.delivery_state, d.policy_version, d.logical_delivery_host_code,
        d.issued_at, d.expires_at, d.consumed_at, d.revoked_at,
        d.download_count, d.first_downloaded_at, d.last_downloaded_at
    """

    _BUNDLE_BY_ID_SQL = f"""
        SELECT {_BUNDLE_COLUMNS}
        FROM nexilabs_auth.credential_bundle AS b
        WHERE b.bundle_id = %s
        LIMIT 1
    """

    _READY_BUNDLE_FOR_PRINCIPAL_SQL = f"""
        SELECT {_BUNDLE_COLUMNS}
        FROM nexilabs_auth.credential_bundle AS b
        JOIN nexilabs_auth.principal_account AS p
          ON p.principal_id = b.principal_id
         AND p.identity_type = 'nexadevs_developer'
        JOIN nexilabs_auth.enigma_profile AS ep
          ON ep.profile_id = b.enigma_profile_id
         AND ep.profile_state = 'ACTIVE'
        JOIN nexilabs_auth.principal_enigma_profile AS pep
          ON pep.principal_id = b.principal_id
         AND pep.profile_id = b.enigma_profile_id
         AND pep.assignment_state = 'ACTIVE'
        WHERE b.principal_id = %s
          AND b.bundle_state = 'READY'
        ORDER BY b.ready_at DESC NULLS LAST
        LIMIT 2
    """

    _ACTIVE_SECRET_SQL = """
        SELECT s.bundle_secret_id, s.bundle_id, s.escrow_provider_code,
               s.encrypted_secret_reference, s.encryption_context_version,
               s.created_at, s.retired_at
        FROM nexilabs_auth.credential_bundle_secret AS s
        WHERE s.bundle_id = %s
          AND s.retired_at IS NULL
        ORDER BY s.created_at DESC
        LIMIT 2
    """

    _DELIVERY_BY_ID_SQL = f"""
        SELECT {_DELIVERY_COLUMNS}
        FROM nexilabs_auth.credential_delivery AS d
        WHERE d.delivery_id = %s
        LIMIT 1
    """

    _ISSUED_DELIVERY_SQL = f"""
        SELECT {_DELIVERY_COLUMNS}
        FROM nexilabs_auth.credential_delivery AS d
        JOIN nexilabs_auth.credential_bundle AS b
          ON b.bundle_id = d.bundle_id
         AND b.bundle_state = 'READY'
        WHERE d.bundle_id = %s
          AND d.delivery_state = 'ISSUED'
        ORDER BY d.issued_at DESC
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
            raise CredentialBundlePersistenceError(f"multiple active {label} records")
        return rows[0] if rows else None

    @classmethod
    def _bundle_record(cls, row: tuple[Any, ...] | None) -> CredentialBundleRecord | None:
        if row is None:
            return None
        return CredentialBundleRecord(
            bundle_id=str(row[0]),
            principal_id=str(row[1]),
            enigma_profile_id=str(row[2]),
            bundle_state=str(row[3]),
            object_provider_code=str(row[4]),
            object_key=str(row[5]),
            content_sha256=str(row[6]),
            byte_size=int(row[7]),
            created_at=cls._iso(row[8]) or "",
            integrity_verified_at=cls._iso(row[9]),
            object_confirmed_at=cls._iso(row[10]),
            ready_at=cls._iso(row[11]),
            expires_at=cls._iso(row[12]) or "",
            retention_until=cls._iso(row[13]) or "",
            invalidated_at=cls._iso(row[14]),
            retired_at=cls._iso(row[15]),
        )

    @classmethod
    def _secret_record(cls, row: tuple[Any, ...] | None) -> CredentialBundleSecretRecord | None:
        if row is None:
            return None
        return CredentialBundleSecretRecord(
            bundle_secret_id=str(row[0]),
            bundle_id=str(row[1]),
            escrow_provider_code=str(row[2]),
            encrypted_secret_reference=str(row[3]),
            encryption_context_version=str(row[4]),
            created_at=cls._iso(row[5]) or "",
            retired_at=cls._iso(row[6]),
        )

    @classmethod
    def _delivery_record(cls, row: tuple[Any, ...] | None) -> CredentialDeliveryRecord | None:
        if row is None:
            return None
        return CredentialDeliveryRecord(
            delivery_id=str(row[0]),
            bundle_id=str(row[1]),
            token_verifier_scheme=str(row[2]),
            token_verifier_version=int(row[3]),
            token_verifier_payload=str(row[4]),
            delivery_state=str(row[5]),
            policy_version=str(row[6]),
            logical_delivery_host_code=str(row[7]),
            issued_at=cls._iso(row[8]) or "",
            expires_at=cls._iso(row[9]) or "",
            consumed_at=cls._iso(row[10]),
            revoked_at=cls._iso(row[11]),
            download_count=int(row[12]),
            first_downloaded_at=cls._iso(row[13]),
            last_downloaded_at=cls._iso(row[14]),
        )

    def bundle_by_id(self, bundle_id: str) -> CredentialBundleRecord | None:
        value = str(bundle_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._BUNDLE_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._bundle_record(row)

    def ready_bundle_for_principal(self, principal_id: str) -> CredentialBundleRecord | None:
        value = str(principal_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._READY_BUNDLE_FOR_PRINCIPAL_SQL, (value,))
                row = self._single(list(cursor.fetchall()), "READY credential bundle")
        return self._bundle_record(row)

    def active_secret_reference(self, bundle_id: str) -> CredentialBundleSecretRecord | None:
        value = str(bundle_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ACTIVE_SECRET_SQL, (value,))
                row = self._single(list(cursor.fetchall()), "credential bundle secret")
        return self._secret_record(row)

    def delivery_by_id(self, delivery_id: str) -> CredentialDeliveryRecord | None:
        value = str(delivery_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._DELIVERY_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._delivery_record(row)

    def issued_delivery_for_bundle(self, bundle_id: str) -> CredentialDeliveryRecord | None:
        value = str(bundle_id).strip()
        if not value:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ISSUED_DELIVERY_SQL, (value,))
                row = self._single(list(cursor.fetchall()), "ISSUED credential delivery")
        return self._delivery_record(row)


__all__ = ["PostgreSQLCredentialBundleAuthority"]
