"""Expected-object and schema-emptiness inspection."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatabaseObjectState:
    schemas: frozenset[str] = frozenset()
    tables: frozenset[str] = frozenset()
    indexes: frozenset[str] = frozenset()
    constraints: frozenset[str] = frozenset()
    views: frozenset[str] = frozenset()
    functions: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class DriftReport:
    missing: tuple[str, ...]
    checked_count: int

    @property
    def is_clean(self) -> bool:
        return not self.missing


@dataclass(frozen=True, slots=True)
class SchemaInventory:
    schema_name: str
    tables: int = 0
    views: int = 0
    materialized_views: int = 0
    sequences: int = 0
    routines: int = 0
    custom_types: int = 0
    foreign_tables: int = 0

    @property
    def is_empty(self) -> bool:
        return sum(
            (
                self.tables,
                self.views,
                self.materialized_views,
                self.sequences,
                self.routines,
                self.custom_types,
                self.foreign_tables,
            )
        ) == 0


_OBJECT_LABELS = {
    "schemas": "schema",
    "tables": "table",
    "indexes": "index",
    "constraints": "constraint",
    "views": "view",
    "functions": "function",
}


def _matches_expected_object(
    field: str,
    expected_name: str,
    present_names: frozenset[str],
) -> bool:
    """Return whether one manifest object is present in inspected database state.

    PostgreSQL index inspection intentionally returns schema-qualified identifiers
    (for example ``reference.ix_name_authority_search``), while existing migration
    manifests use unqualified index names. Exact matching remains authoritative for
    every object type. Only unqualified index expectations receive basename matching.
    """

    if expected_name in present_names:
        return True

    if field == "indexes" and "." not in expected_name:
        return any(
            actual_name.rsplit(".", 1)[-1] == expected_name
            for actual_name in present_names
        )

    return False


class MigrationDriftInspector:
    def __init__(self, adapter):
        self.adapter = adapter

    def inspect_expected(self, plan):
        actual = self.adapter.inspect_database_objects()
        missing: list[str] = []
        checked = 0
        mapping = (
            ("schemas", actual.schemas),
            ("tables", actual.tables),
            ("indexes", actual.indexes),
            ("constraints", actual.constraints),
            ("views", actual.views),
            ("functions", actual.functions),
        )

        for definition in plan.forward_order:
            expected = definition.expected_objects
            for field, present in mapping:
                for name in getattr(expected, field):
                    checked += 1
                    if not _matches_expected_object(field, name, present):
                        missing.append(f"{_OBJECT_LABELS[field]}:{name}")

        return DriftReport(tuple(sorted(set(missing))), checked)

    def inspect_schema(self, schema_name):
        return self.adapter.inspect_schema_inventory(schema_name)
