from infrastructure.database.read.nngla import PostgreSQLNNGLAReadRepository


class DispatchCursor:
    def __init__(self):
        self.rows = []
        self.row = None
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        compact = " ".join(sql.split())
        self.row = None
        if "SUM(a.row_count)" in compact and "GROUP BY d.dataset_id" in compact:
            self.rows = [
                ("dataset:novegeo:places:v001:700", "1", 700),
                ("dataset:novegeo:administrative-areas:v001:192", "1", 192),
                ("dataset:novegeo:geographic-features:v001:21", "1", 21),
                ("dataset:novegeo:roads:v001:900", "1", 900),
            ]
        elif "UNION ALL" in compact and "nngla_place_reference" in compact:
            self.rows = [
                ("PLACE", 700),
                ("ADMINISTRATIVE_AREA", 192),
                ("GEOGRAPHIC_FEATURE", 21),
                ("ROAD", 350),
                ("ADDRESS", 0),
                ("PARCEL", 0),
            ]
        elif "GROUP BY record_family" in compact:
            self.rows = []
        elif "MAX(read_model_version)" in compact:
            self.row = (1,)
            self.rows = []
        elif "nngla_canonical_crosswalk" in compact and "SUM(a.row_count)" in compact:
            self.row = (2411, 2411)
            self.rows = []
        elif "FROM geography.nngla_spatial_read_projection_v1" in compact and "ORDER BY subject_id" in compact:
            self.rows = []
        else:
            raise AssertionError(f"Unexpected SQL: {compact}")

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_ref = cursor

    def cursor(self):
        return self.cursor_ref


class Context:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self):
        self.cursor = DispatchCursor()
        self.read_only_calls = []

    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        return Context(FakeConnection(self.cursor))


def test_postgresql_nngla_repository_reads_exact_counts_and_completed_coordinate_migration_read_only():
    pool = FakePool()
    repository = PostgreSQLNNGLAReadRepository(pool, runtime_mode="simulation")

    counts = repository.family_counts()
    assert counts["PLACE"].canonical_count == 700
    assert counts["ROAD"].source_count == 900
    assert counts["ROAD"].canonical_count == 350
    assert counts["GEOGRAPHIC_FEATURE"].canonical_count == 21
    assert counts["ADDRESS"].source_count == 0
    assert repository.coordinate_migration_status() == "EXECUTED"
    assert repository.read_model_version() == 1
    assert repository.public_items("PLACE") == ()
    assert pool.read_only_calls and all(pool.read_only_calls)


def test_postgresql_nngla_repository_rejects_cross_runtime_or_unknown_runtime_configuration():
    pool = FakePool()
    try:
        PostgreSQLNNGLAReadRepository(pool, runtime_mode="shared_reference")
    except ValueError as exc:
        assert "simulation or production" in str(exc)
    else:
        raise AssertionError("shared_reference must not be accepted for NNGLA public projection runtime")
