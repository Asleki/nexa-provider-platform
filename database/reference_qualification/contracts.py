"""Immutable contracts for M009.13.10 reference-registry qualification."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from collections.abc import Mapping


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return value.strip()


def _tuple_text(values: object, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str) or not isinstance(values, (tuple, list, set, frozenset)):
        raise TypeError(f"{field_name} must be an iterable of text values.")
    output: list[str] = []
    for raw in values:
        item = _required_text(raw, field_name)
        if item not in output:
            output.append(item)
    return tuple(output)


@dataclass(frozen=True, slots=True)
class SchemaColumn:
    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    nullable: bool
    default_expression: str | None = None
    ordinal_position: int = 1

    def __post_init__(self) -> None:
        for name in ("schema_name", "table_name", "column_name", "data_type"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        if not isinstance(self.nullable, bool):
            raise TypeError("nullable must be boolean.")
        if not isinstance(self.ordinal_position, int) or self.ordinal_position < 1:
            raise ValueError("ordinal_position must be a positive integer.")


@dataclass(frozen=True, slots=True)
class SchemaConstraint:
    schema_name: str
    table_name: str
    constraint_name: str
    constraint_type: str
    definition: str

    def __post_init__(self) -> None:
        for name in ("schema_name", "table_name", "constraint_name", "constraint_type", "definition"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class SchemaIndex:
    schema_name: str
    table_name: str
    index_name: str
    definition: str

    def __post_init__(self) -> None:
        for name in ("schema_name", "table_name", "index_name", "definition"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class SchemaTrigger:
    schema_name: str
    table_name: str
    trigger_name: str
    definition: str

    def __post_init__(self) -> None:
        for name in ("schema_name", "table_name", "trigger_name", "definition"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class PostgreSQLSchemaReport:
    database_name: str
    inspected_schemas: tuple[str, ...]
    tables: tuple[str, ...]
    views: tuple[str, ...]
    columns: tuple[SchemaColumn, ...]
    constraints: tuple[SchemaConstraint, ...]
    indexes: tuple[SchemaIndex, ...]
    triggers: tuple[SchemaTrigger, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "database_name", _required_text(self.database_name, "database_name"))
        object.__setattr__(self, "inspected_schemas", _tuple_text(self.inspected_schemas, "inspected_schemas"))
        object.__setattr__(self, "tables", _tuple_text(self.tables, "tables"))
        object.__setattr__(self, "views", _tuple_text(self.views, "views"))
        for field_name in ("columns", "constraints", "indexes", "triggers"):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))


@dataclass(frozen=True, slots=True)
class QualificationFinding:
    code: str
    status: str
    message: str
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _required_text(self.code, "code"))
        status = _required_text(self.status, "status").lower()
        if status not in {"passed", "warning", "failed", "reserved"}:
            raise ValueError("status is unsupported.")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "message", _required_text(self.message, "message"))
        if not isinstance(self.details, Mapping):
            raise TypeError("details must be a mapping.")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class ProductionNameQualificationRequest:
    raw_name_value: str
    requested_name_kind: str
    sex_usage: str
    submitter_actor_id: str
    approver_actor_id: str
    qualification_id: str
    origin_label: str | None = None
    language_label: str | None = None
    community_label: str | None = None
    script_code: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "raw_name_value", "requested_name_kind", "sex_usage",
            "submitter_actor_id", "approver_actor_id", "qualification_id",
        ):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        if self.submitter_actor_id == self.approver_actor_id:
            raise ValueError("submitter and approver must be different actors.")
        for name in ("origin_label", "language_label", "community_label", "script_code", "notes"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str):
                    raise TypeError(f"{name} must be text or None.")
                object.__setattr__(self, name, value.strip() or None)


@dataclass(frozen=True, slots=True)
class ProductionNameQualificationReport:
    qualification_id: str
    canonical_name_id: str
    canonical_value: str
    search_value: str
    name_kind: str
    runtime_mode: str
    first_outcome: str
    duplicate_outcome: str
    production_match_count: int
    simulation_match_count: int
    findings: tuple[QualificationFinding, ...]

    def __post_init__(self) -> None:
        for name in (
            "qualification_id", "canonical_name_id", "canonical_value", "search_value",
            "name_kind", "runtime_mode", "first_outcome", "duplicate_outcome",
        ):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        for name in ("production_match_count", "simulation_match_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        object.__setattr__(self, "findings", tuple(self.findings))

    @property
    def passed(self) -> bool:
        return all(item.status != "failed" for item in self.findings)


__all__ = [
    "SchemaColumn", "SchemaConstraint", "SchemaIndex", "SchemaTrigger",
    "PostgreSQLSchemaReport", "QualificationFinding",
    "ProductionNameQualificationRequest", "ProductionNameQualificationReport",
]
