from registries.nngla.migration_architecture.persistence import (
    PostgreSQLExecutionRepository,
)
from registries.nngla.migration_architecture.source_catalogue import load_source


class RecordingCursor:
    def __init__(self, statements):
        self.statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.statements.append((sql, params))


class RecordingConnection:
    def __init__(self):
        self.statements = []

    def cursor(self):
        return RecordingCursor(self.statements)


def test_bundle16c_unmapped_place_without_geometry_reference_persists_null_geometry():
    snapshot = load_source("places")
    record = next(
        record
        for record in snapshot.records
        if record.source_id == "NGP-000001"
    )

    assert record.payload["spatial_assignment_status"] == "UNMAPPED_PENDING_ASSOCIATION"
    assert "geometry_reference" not in record.payload

    connection = RecordingConnection()
    repository = PostgreSQLExecutionRepository(
        connection,
        database_name="npp_dev",
        environment_name="development",
    )

    repository.persist_canonical(
        snapshot.descriptor,
        record,
        "NG-PLC-000001",
        "production",
    )

    assert len(connection.statements) == 2

    name_sql, name_params = connection.statements[0]
    place_sql, place_params = connection.statements[1]

    assert "nngla_geographic_name" in name_sql
    assert "nngla_place_reference" in place_sql

    assert name_params[0] == "NG-NAM-SET-000001"

    assert place_params[0] == "NG-PLC-000001"
    assert place_params[1] == "NGP-000001"
    assert place_params[6] == "UNMAPPED_PENDING_ASSOCIATION"
    assert place_params[7] is None
