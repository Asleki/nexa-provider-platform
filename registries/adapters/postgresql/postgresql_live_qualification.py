"""
============================================================
Nexa Provider Platform
File: registries/adapters/postgresql/postgresql_live_qualification.py
Layer: Registry PostgreSQL Qualification Adapter
Milestone: M009.11.A — PostgreSQL Live Connectivity Smoke Test
============================================================

Purpose
-------
Performs a read-only qualification of the live PostgreSQL partner.

The component verifies:
- external connection configuration;
- NPP operational runtime selection;
- database authentication and server identity;
- expected Name Catalogue schema structures;
- Python-controlled diagnostics and safe cleanup.

It never inserts, updates, or deletes catalogue records. Python
remains authoritative for runtime interpretation and domain rules;
PostgreSQL is inspected only as the persistence and integrity layer.
============================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from shared.runtime.operation_runtime import (
    ENV_OPERATION_RUNTIME_MODE,
    OperationRuntimeMode,
    SUPPORTED_OPERATION_RUNTIME_MODES,
)


ENV_POSTGRES_HOST: Final[str] = "NPP_POSTGRES_HOST"
ENV_POSTGRES_PORT: Final[str] = "NPP_POSTGRES_PORT"
ENV_POSTGRES_DATABASE: Final[str] = "NPP_POSTGRES_DATABASE"
ENV_POSTGRES_USER: Final[str] = "NPP_POSTGRES_USER"
ENV_POSTGRES_PASSWORD: Final[str] = "NPP_POSTGRES_PASSWORD"
ENV_POSTGRES_SSLMODE: Final[str] = "NPP_POSTGRES_SSLMODE"
ENV_POSTGRES_CONNECT_TIMEOUT: Final[str] = "NPP_POSTGRES_CONNECT_TIMEOUT"

_REQUIRED_ENVIRONMENT_KEYS: Final[tuple[str, ...]] = (
    ENV_POSTGRES_HOST,
    ENV_POSTGRES_DATABASE,
    ENV_POSTGRES_USER,
    ENV_POSTGRES_PASSWORD,
    ENV_OPERATION_RUNTIME_MODE,
)

_EXPECTED_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "name_id",
        "canonical_value",
        "search_value",
        "name_kind",
        "status",
        "runtime_mode",
        "schema_version",
        "created_at",
    }
)
_EXPECTED_UNIQUE_CONSTRAINT: Final[str] = "uq_canonical_name_identity"
_EXPECTED_RUNTIME_INDEX: Final[str] = "ix_canonical_name_runtime_kind_search"


class PostgreSQLQualificationError(RuntimeError):
    """Base error for qualification failures."""

    error_code: str = "NPP_POSTGRES_QUALIFICATION_FAILED"


class PostgreSQLQualificationConfigurationError(PostgreSQLQualificationError):
    """Raised before connection when required configuration is invalid."""

    error_code = "NPP_POSTGRES_CONFIGURATION_INVALID"


class PostgreSQLQualificationConnectionError(PostgreSQLQualificationError):
    """Raised when the live database cannot be reached or queried."""

    error_code = "NPP_POSTGRES_CONNECTION_FAILED"


class PostgreSQLQualificationSchemaError(PostgreSQLQualificationError):
    """Raised when the expected live schema contract is absent."""

    error_code = "NPP_POSTGRES_SCHEMA_QUALIFICATION_FAILED"


@dataclass(frozen=True, slots=True)
class PostgreSQLQualificationConfig:
    """Validated connection and runtime configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str
    sslmode: str
    connect_timeout: int
    runtime_mode: OperationRuntimeMode

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str],
    ) -> "PostgreSQLQualificationConfig":
        """Build configuration without hard-coding credentials."""

        missing = [
            key
            for key in _REQUIRED_ENVIRONMENT_KEYS
            if not str(environment.get(key, "")).strip()
        ]
        if missing:
            raise PostgreSQLQualificationConfigurationError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + "."
            )

        runtime_raw = environment[ENV_OPERATION_RUNTIME_MODE]
        try:
            runtime_mode = OperationRuntimeMode.parse(runtime_raw)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(SUPPORTED_OPERATION_RUNTIME_MODES)
            raise PostgreSQLQualificationConfigurationError(
                f"Invalid {ENV_OPERATION_RUNTIME_MODE}: {runtime_raw!r}. "
                f"Valid modes: {valid}."
            ) from exc

        port = _positive_int(
            environment.get(ENV_POSTGRES_PORT, "5432"),
            ENV_POSTGRES_PORT,
        )
        connect_timeout = _positive_int(
            environment.get(ENV_POSTGRES_CONNECT_TIMEOUT, "10"),
            ENV_POSTGRES_CONNECT_TIMEOUT,
        )

        sslmode = str(environment.get(ENV_POSTGRES_SSLMODE, "require")).strip().lower()
        if sslmode not in {
            "disable",
            "allow",
            "prefer",
            "require",
            "verify-ca",
            "verify-full",
        }:
            raise PostgreSQLQualificationConfigurationError(
                f"Invalid {ENV_POSTGRES_SSLMODE}: {sslmode!r}."
            )

        return cls(
            host=str(environment[ENV_POSTGRES_HOST]).strip(),
            port=port,
            database=str(environment[ENV_POSTGRES_DATABASE]).strip(),
            user=str(environment[ENV_POSTGRES_USER]).strip(),
            password=str(environment[ENV_POSTGRES_PASSWORD]),
            sslmode=sslmode,
            connect_timeout=connect_timeout,
            runtime_mode=runtime_mode,
        )

    def connection_kwargs(self) -> dict[str, object]:
        """Return DB-driver arguments; never use this for logging."""

        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
            "sslmode": self.sslmode,
            "connect_timeout": self.connect_timeout,
        }

    def safe_summary(self) -> dict[str, object]:
        """Return non-sensitive configuration suitable for diagnostics."""

        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "sslmode": self.sslmode,
            "connect_timeout": self.connect_timeout,
            "runtime_mode": self.runtime_mode.value,
        }


@dataclass(frozen=True, slots=True)
class PostgreSQLQualificationResult:
    """Structured result returned after a successful qualification."""

    runtime_mode: str
    database_name: str
    database_user: str
    server_version: str
    schema_name: str
    table_name: str
    columns: tuple[str, ...]
    unique_constraint_name: str
    runtime_index_name: str


class PostgreSQLLiveQualifier:
    """Run the same read-only qualification under either NPP runtime."""

    def __init__(self, connection_factory: Callable[..., object]) -> None:
        if not callable(connection_factory):
            raise TypeError("connection_factory must be callable.")
        self._connection_factory = connection_factory

    def qualify(
        self,
        config: PostgreSQLQualificationConfig,
    ) -> PostgreSQLQualificationResult:
        if not isinstance(config, PostgreSQLQualificationConfig):
            raise TypeError("config must be PostgreSQLQualificationConfig.")

        connection: object | None = None
        closed = False
        try:
            connection = self._connection_factory(**config.connection_kwargs())
            if connection is None:
                raise PostgreSQLQualificationConnectionError(
                    "Connection factory returned no connection."
                )

            identity = self._fetch_one(
                connection,
                "SELECT current_database(), current_user, version()",
            )
            if len(identity) < 3:
                raise PostgreSQLQualificationConnectionError(
                    "PostgreSQL identity query returned an incomplete result."
                )

            columns = self._fetch_column_values(
                connection,
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                ("reference", "canonical_name"),
            )
            missing_columns = sorted(_EXPECTED_COLUMNS.difference(columns))
            if missing_columns:
                raise PostgreSQLQualificationSchemaError(
                    "reference.canonical_name is missing expected columns: "
                    + ", ".join(missing_columns)
                    + "."
                )

            constraints = self._fetch_column_values(
                connection,
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = %s
                  AND table_name = %s
                  AND constraint_type = 'UNIQUE'
                ORDER BY constraint_name
                """,
                ("reference", "canonical_name"),
            )
            if _EXPECTED_UNIQUE_CONSTRAINT not in constraints:
                raise PostgreSQLQualificationSchemaError(
                    f"Missing unique constraint {_EXPECTED_UNIQUE_CONSTRAINT!r}."
                )

            indexes = self._fetch_column_values(
                connection,
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = %s AND tablename = %s
                ORDER BY indexname
                """,
                ("reference", "canonical_name"),
            )
            if _EXPECTED_RUNTIME_INDEX not in indexes:
                raise PostgreSQLQualificationSchemaError(
                    f"Missing runtime index {_EXPECTED_RUNTIME_INDEX!r}."
                )

            return PostgreSQLQualificationResult(
                runtime_mode=config.runtime_mode.value,
                database_name=str(identity[0]),
                database_user=str(identity[1]),
                server_version=str(identity[2]),
                schema_name="reference",
                table_name="canonical_name",
                columns=tuple(columns),
                unique_constraint_name=_EXPECTED_UNIQUE_CONSTRAINT,
                runtime_index_name=_EXPECTED_RUNTIME_INDEX,
            )
        except PostgreSQLQualificationError:
            raise
        except Exception as exc:
            raise PostgreSQLQualificationConnectionError(
                f"{type(exc).__name__}: {exc}"
            ) from exc
        finally:
            if connection is not None:
                try:
                    connection.close()  # type: ignore[attr-defined]
                    closed = True
                except Exception:
                    closed = False

            # Result objects are immutable. The CLI verifies closure separately
            # through the connection object when supported by the driver.
            _ = closed

    @staticmethod
    def _fetch_one(
        connection: object,
        sql: str,
        params: Sequence[object] | None = None,
    ) -> tuple[object, ...]:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if row is None:
                raise PostgreSQLQualificationConnectionError(
                    "PostgreSQL query returned no row."
                )
            return tuple(row)
        finally:
            cursor.close()

    @classmethod
    def _fetch_column_values(
        cls,
        connection: object,
        sql: str,
        params: Sequence[object],
    ) -> tuple[str, ...]:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        try:
            cursor.execute(sql, params)
            return tuple(str(row[0]) for row in cursor.fetchall())
        finally:
            cursor.close()


def _positive_int(raw: object, field_name: str) -> int:
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise PostgreSQLQualificationConfigurationError(
            f"{field_name} must be an integer."
        ) from exc
    if value < 1:
        raise PostgreSQLQualificationConfigurationError(
            f"{field_name} must be greater than zero."
        )
    return value


def load_psycopg_connect() -> Callable[..., object]:
    """Load psycopg lazily so ordinary repository imports remain unaffected."""

    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PostgreSQLQualificationConfigurationError(
            "The psycopg driver is not installed. Install psycopg[binary] "
            "before running the live qualification."
        ) from exc
    return psycopg.connect


def render_success_report(
    config: PostgreSQLQualificationConfig,
    result: PostgreSQLQualificationResult,
) -> str:
    """Render a Python-owned success report without exposing secrets."""

    safe = config.safe_summary()
    lines = [
        "=" * 64,
        "NPP M009.11.A — AWS PostgreSQL Live Qualification",
        "=" * 64,
        f"Runtime mode: {result.runtime_mode.upper()}",
        f"Database host: {safe['host']}",
        f"Database port: {safe['port']}",
        f"Database name: {result.database_name}",
        f"Authenticated user: {result.database_user}",
        f"SSL mode: {safe['sslmode']}",
        "Connection: PASS",
        f"Schema: {result.schema_name}.{result.table_name}",
        f"Runtime column: {'PASS' if 'runtime_mode' in result.columns else 'FAIL'}",
        f"Identity constraint: {result.unique_constraint_name}",
        f"Runtime index: {result.runtime_index_name}",
        "Data mutation: NONE (read-only qualification)",
        "Connection cleanup: requested",
        f"Server version: {result.server_version}",
        "=" * 64,
        "QUALIFICATION PASSED",
    ]
    return "\n".join(lines)


def render_error_report(error: BaseException) -> str:
    """Render a Python-owned diagnostic for terminal display."""

    code = getattr(error, "error_code", "NPP_POSTGRES_UNEXPECTED_ERROR")
    return "\n".join(
        [
            "=" * 64,
            "NPP M009.11.A — AWS PostgreSQL Live Qualification",
            "=" * 64,
            "QUALIFICATION FAILED",
            f"Error code: {code}",
            f"Error type: {type(error).__name__}",
            f"Details: {error}",
            "No database password was written to this report.",
            "No Name Catalogue record was inserted, updated, or deleted.",
            "=" * 64,
        ]
    )


__all__ = [
    "ENV_POSTGRES_CONNECT_TIMEOUT",
    "ENV_POSTGRES_DATABASE",
    "ENV_POSTGRES_HOST",
    "ENV_POSTGRES_PASSWORD",
    "ENV_POSTGRES_PORT",
    "ENV_POSTGRES_SSLMODE",
    "ENV_POSTGRES_USER",
    "PostgreSQLLiveQualifier",
    "PostgreSQLQualificationConfig",
    "PostgreSQLQualificationConfigurationError",
    "PostgreSQLQualificationConnectionError",
    "PostgreSQLQualificationError",
    "PostgreSQLQualificationResult",
    "PostgreSQLQualificationSchemaError",
    "load_psycopg_connect",
    "render_error_report",
    "render_success_report",
]
