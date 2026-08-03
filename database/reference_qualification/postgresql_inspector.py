"""Read-only PostgreSQL structural inspection for reference registries."""
from __future__ import annotations

from .contracts import (
    PostgreSQLSchemaReport,
    SchemaColumn,
    SchemaConstraint,
    SchemaIndex,
    SchemaTrigger,
)
from .errors import SchemaInspectionError


class PostgreSQLReferenceSchemaInspector:
    """Inspect schemas without changing database state."""

    def __init__(self, connection_factory) -> None:
        if not callable(connection_factory):
            raise TypeError("connection_factory must be callable.")
        self._connection_factory = connection_factory

    def inspect(self, schemas: tuple[str, ...] = ("reference", "migration_control")) -> PostgreSQLSchemaReport:
        normalized = tuple(dict.fromkeys(item.strip() for item in schemas if isinstance(item, str) and item.strip()))
        if not normalized:
            raise ValueError("at least one schema is required.")
        conn = self._connection_factory()
        try:
            cur = conn.cursor()
            cur.execute("SELECT current_database()")
            database_name = str(cur.fetchone()[0])

            cur.execute(
                """
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = ANY(%s)
                ORDER BY table_schema, table_name
                """,
                (list(normalized),),
            )
            table_rows = cur.fetchall()
            tables = tuple(f"{schema}.{name}" for schema, name, kind in table_rows if kind == "BASE TABLE")
            views = tuple(f"{schema}.{name}" for schema, name, kind in table_rows if kind == "VIEW")

            cur.execute(
                """
                SELECT table_schema, table_name, column_name, data_type,
                       is_nullable, column_default, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = ANY(%s)
                ORDER BY table_schema, table_name, ordinal_position
                """,
                (list(normalized),),
            )
            columns = tuple(
                SchemaColumn(schema, table, column, data_type, nullable == "YES", default, int(position))
                for schema, table, column, data_type, nullable, default, position in cur.fetchall()
            )

            cur.execute(
                """
                SELECT n.nspname, c.relname, con.conname,
                       CASE con.contype
                         WHEN 'p' THEN 'PRIMARY KEY'
                         WHEN 'u' THEN 'UNIQUE'
                         WHEN 'f' THEN 'FOREIGN KEY'
                         WHEN 'c' THEN 'CHECK'
                         WHEN 'x' THEN 'EXCLUSION'
                         ELSE con.contype::text
                       END,
                       pg_get_constraintdef(con.oid, true)
                FROM pg_constraint con
                JOIN pg_class c ON c.oid = con.conrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = ANY(%s)
                ORDER BY n.nspname, c.relname, con.conname
                """,
                (list(normalized),),
            )
            constraints = tuple(SchemaConstraint(*row) for row in cur.fetchall())

            cur.execute(
                """
                SELECT schemaname, tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = ANY(%s)
                ORDER BY schemaname, tablename, indexname
                """,
                (list(normalized),),
            )
            indexes = tuple(SchemaIndex(*row) for row in cur.fetchall())

            cur.execute(
                """
                SELECT event_object_schema, event_object_table, trigger_name,
                       action_statement
                FROM information_schema.triggers
                WHERE event_object_schema = ANY(%s)
                ORDER BY event_object_schema, event_object_table, trigger_name
                """,
                (list(normalized),),
            )
            triggers = tuple(SchemaTrigger(*row) for row in cur.fetchall())

            return PostgreSQLSchemaReport(
                database_name=database_name,
                inspected_schemas=normalized,
                tables=tables,
                views=views,
                columns=columns,
                constraints=constraints,
                indexes=indexes,
                triggers=triggers,
            )
        except Exception as exc:
            raise SchemaInspectionError("PostgreSQL reference-schema inspection failed.") from exc
        finally:
            close = getattr(conn, "close", None)
            if callable(close):
                close()


__all__ = ["PostgreSQLReferenceSchemaInspector"]
