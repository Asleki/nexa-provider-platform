from database.reference_qualification.postgresql_inspector import PostgreSQLReferenceSchemaInspector


class Cursor:
    def __init__(self):
        self.rows = []

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        if "current_database()" in normalized:
            self.rows = [("npp_dev",)]
        elif "FROM information_schema.tables" in normalized:
            self.rows = [("reference", "canonical_name", "BASE TABLE"), ("reference", "active_names", "VIEW")]
        elif "FROM information_schema.columns" in normalized:
            self.rows = [("reference", "canonical_name", "name_id", "text", "NO", None, 1)]
        elif "FROM pg_constraint" in normalized:
            self.rows = [("reference", "canonical_name", "canonical_name_pkey", "PRIMARY KEY", "PRIMARY KEY (name_id)")]
        elif "FROM pg_indexes" in normalized:
            self.rows = [("reference", "canonical_name", "canonical_name_pkey", "CREATE UNIQUE INDEX ...")]
        elif "FROM information_schema.triggers" in normalized:
            self.rows = []
        else:
            raise AssertionError(normalized)

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return list(self.rows)


class Connection:
    def __init__(self):
        self.cur = Cursor()
        self.closed = False

    def cursor(self):
        return self.cur

    def close(self):
        self.closed = True


def test_postgresql_inspector_returns_deterministic_read_only_report():
    conn = Connection()
    report = PostgreSQLReferenceSchemaInspector(lambda: conn).inspect(("reference",))
    assert report.database_name == "npp_dev"
    assert report.tables == ("reference.canonical_name",)
    assert report.views == ("reference.active_names",)
    assert report.columns[0].column_name == "name_id"
    assert report.constraints[0].constraint_type == "PRIMARY KEY"
    assert conn.closed is True
