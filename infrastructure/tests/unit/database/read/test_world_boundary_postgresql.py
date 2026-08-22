import json

import pytest

from infrastructure.database.read.world_boundary import (
    PostgreSQLWorldBoundaryRepository,
    WorldBoundaryAuthorityError,
)


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.sql = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        self.sql = sql

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.cursor_ref = FakeCursor(row)

    def cursor(self):
        return self.cursor_ref


class FakeContext:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, row):
        self.connection_ref = FakeConnection(row)
        self.read_only_calls = []

    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        return FakeContext(self.connection_ref)


def boundary_row(**overrides):
    values = [
        "publication:novegeo:world-boundary:v002",
        "boundary:novegeo:sovereign",
        2,
        "dataset:novegeo:world-boundary",
        2,
        "crs:novegeo:geographic",
        1,
        "EPSG",
        "4326",
        ["longitude", "latitude"],
        "decimal_degrees",
        json.dumps({"type": "MultiPolygon", "coordinates": [[[[29.05, -7.0], [30.0, -7.0], [29.05, -7.0]]]]}),
        29.05,
        -7.717467,
        44.805229,
        7.85,
        "a" * 64,
        "b" * 64,
        "b" * 64,
        "shared_reference",
        "shared_reference",
        "shared_reference",
        "public",
        "public",
        "public",
        "active",
        "active",
        "qualified",
        "dataset:novegeo:world-boundary",
    ]
    index = {
        "publication_content_sha256": 18,
        "source_dataset_id": 28,
        "publication_runtime_mode": 20,
        "source_runtime_mode": 21,
        "source_visibility": 24,
        "qualification_decision": 27,
    }
    for key, value in overrides.items():
        values[index[key]] = value
    return tuple(values)


def test_postgresql_world_boundary_repository_reads_active_v002_with_read_only_transaction():
    pool = FakePool(boundary_row())
    publication = PostgreSQLWorldBoundaryRepository(pool).get_active()

    assert pool.read_only_calls == [True]
    assert publication.identity.boundary_id == "boundary:novegeo:sovereign"
    assert publication.identity.version == 2
    assert publication.dataset_version == 2
    assert publication.runtime_mode == "shared_reference"
    assert publication.geometry["type"] == "MultiPolygon"
    assert publication.extent == (29.05, -7.717467, 44.805229, 7.85)
    sql = pool.connection_ref.cursor_ref.sql
    assert "boundary_qualification" in sql
    assert "boundary_publication" in sql
    assert "ST_AsGeoJSON" in sql


def test_postgresql_world_boundary_repository_returns_none_when_no_published_active_boundary_exists():
    assert PostgreSQLWorldBoundaryRepository(FakePool(None)).get_active() is None


def test_postgresql_world_boundary_repository_accepts_distinct_geometry_and_publication_hashes():
    # v002 intentionally stores the authoritative boundary/source content hash
    # separately from the publication-manifest hash.
    publication = PostgreSQLWorldBoundaryRepository(
        FakePool(boundary_row(publication_content_sha256="c" * 64))
    ).get_active()
    assert publication.content_sha256 == "b" * 64


def test_postgresql_world_boundary_repository_is_read_only():
    repository = PostgreSQLWorldBoundaryRepository(FakePool(boundary_row()))
    with pytest.raises(RuntimeError, match="read-only"):
        repository.save(object())
