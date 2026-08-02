import pytest

from registries.adapters.postgresql.postgresql_live_qualification import (
    PostgreSQLLiveQualifier,
    PostgreSQLQualificationConfig,
    PostgreSQLQualificationConfigurationError,
    PostgreSQLQualificationConnectionError,
    PostgreSQLQualificationSchemaError,
    render_error_report,
    render_success_report,
)


BASE_ENV = {
    "NPP_POSTGRES_HOST": "example.rds.amazonaws.com",
    "NPP_POSTGRES_PORT": "5432",
    "NPP_POSTGRES_DATABASE": "npp_dev",
    "NPP_POSTGRES_USER": "npp_admin",
    "NPP_POSTGRES_PASSWORD": "secret-value",
    "NPP_POSTGRES_SSLMODE": "require",
    "NPP_POSTGRES_CONNECT_TIMEOUT": "10",
    "NPP_RUNTIME_MODE": "simulation",
}


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []
        self.closed = False

    def execute(self, sql, params=None):
        self.connection.executed.append((" ".join(sql.split()), params))
        normalized = " ".join(sql.split()).lower()
        if "current_database()" in normalized:
            self.rows = [("npp_dev", "npp_admin", "PostgreSQL test server")]
        elif "information_schema.columns" in normalized:
            self.rows = [
                ("name_id",),
                ("canonical_value",),
                ("search_value",),
                ("name_kind",),
                ("status",),
                ("runtime_mode",),
                ("schema_version",),
                ("created_at",),
            ]
        elif "information_schema.table_constraints" in normalized:
            self.rows = [("uq_canonical_name_identity",)]
        elif "from pg_indexes" in normalized:
            self.rows = [("ix_canonical_name_runtime_kind_search",)]
        else:
            raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


def make_factory(connection, calls):
    def factory(**kwargs):
        calls.append(kwargs)
        return connection

    return factory


def test_configuration_loads_simulation_and_masks_password_from_summary():
    config = PostgreSQLQualificationConfig.from_environment(BASE_ENV)
    assert config.runtime_mode.value == "simulation"
    assert config.connection_kwargs()["password"] == "secret-value"
    assert "password" not in config.safe_summary()
    assert "secret-value" not in repr(config.safe_summary())


def test_configuration_switches_to_production_without_source_change():
    config = PostgreSQLQualificationConfig.from_environment(
        {**BASE_ENV, "NPP_RUNTIME_MODE": "production"}
    )
    assert config.runtime_mode.value == "production"


def test_invalid_runtime_is_rejected_before_connection():
    calls = []
    with pytest.raises(PostgreSQLQualificationConfigurationError):
        PostgreSQLQualificationConfig.from_environment(
            {**BASE_ENV, "NPP_RUNTIME_MODE": "invalid"}
        )
    assert calls == []


def test_missing_credentials_are_reported_by_python():
    environment = dict(BASE_ENV)
    environment.pop("NPP_POSTGRES_PASSWORD")
    with pytest.raises(
        PostgreSQLQualificationConfigurationError,
        match="NPP_POSTGRES_PASSWORD",
    ):
        PostgreSQLQualificationConfig.from_environment(environment)


@pytest.mark.parametrize("runtime_mode", ["simulation", "production"])
def test_live_qualification_route_is_identical_for_both_runtimes(runtime_mode):
    config = PostgreSQLQualificationConfig.from_environment(
        {**BASE_ENV, "NPP_RUNTIME_MODE": runtime_mode}
    )
    connection = FakeConnection()
    calls = []
    result = PostgreSQLLiveQualifier(
        make_factory(connection, calls)
    ).qualify(config)

    assert result.runtime_mode == runtime_mode
    assert result.database_name == "npp_dev"
    assert result.database_user == "npp_admin"
    assert "runtime_mode" in result.columns
    assert result.unique_constraint_name == "uq_canonical_name_identity"
    assert result.runtime_index_name == "ix_canonical_name_runtime_kind_search"
    assert connection.closed is True
    assert calls[0]["sslmode"] == "require"
    assert calls[0]["connect_timeout"] == 10
    assert calls[0]["password"] == "secret-value"


def test_qualification_is_read_only():
    config = PostgreSQLQualificationConfig.from_environment(BASE_ENV)
    connection = FakeConnection()
    PostgreSQLLiveQualifier(lambda **_: connection).qualify(config)
    statements = " ".join(sql for sql, _ in connection.executed).upper()
    for mutation in ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP ", "CREATE "):
        assert mutation not in statements


def test_missing_runtime_column_fails_schema_qualification_and_closes_connection():
    class MissingRuntimeCursor(FakeCursor):
        def execute(self, sql, params=None):
            super().execute(sql, params)
            if "information_schema.columns" in " ".join(sql.split()).lower():
                self.rows = [row for row in self.rows if row[0] != "runtime_mode"]

    class MissingRuntimeConnection(FakeConnection):
        def cursor(self):
            return MissingRuntimeCursor(self)

    config = PostgreSQLQualificationConfig.from_environment(BASE_ENV)
    connection = MissingRuntimeConnection()
    with pytest.raises(PostgreSQLQualificationSchemaError, match="runtime_mode"):
        PostgreSQLLiveQualifier(lambda **_: connection).qualify(config)
    assert connection.closed is True


def test_driver_failure_becomes_npp_connection_error():
    config = PostgreSQLQualificationConfig.from_environment(BASE_ENV)

    def fail(**kwargs):
        raise OSError("network route unavailable")

    with pytest.raises(
        PostgreSQLQualificationConnectionError,
        match="network route unavailable",
    ):
        PostgreSQLLiveQualifier(fail).qualify(config)


def test_reports_are_python_owned_and_do_not_expose_password():
    config = PostgreSQLQualificationConfig.from_environment(BASE_ENV)
    connection = FakeConnection()
    result = PostgreSQLLiveQualifier(lambda **_: connection).qualify(config)
    success = render_success_report(config, result)
    error = render_error_report(
        PostgreSQLQualificationConnectionError("authentication failed")
    )

    assert "QUALIFICATION PASSED" in success
    assert "SIMULATION" in success
    assert "secret-value" not in success
    assert "NPP_POSTGRES_CONNECTION_FAILED" in error
    assert "authentication failed" in error
    assert "secret-value" not in error
