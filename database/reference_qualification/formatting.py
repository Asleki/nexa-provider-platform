"""Human-readable formatting for M009.13.10 reports."""
from __future__ import annotations

from database.migration_control.formatting import format_json
from .contracts import PostgreSQLSchemaReport, ProductionNameQualificationReport


def format_schema_report(report: PostgreSQLSchemaReport) -> str:
    lines = [
        "POSTGRESQL REFERENCE SCHEMA QUALIFICATION",
        "=" * 72,
        f"Database: {report.database_name}",
        f"Schemas: {', '.join(report.inspected_schemas)}",
        f"Tables: {len(report.tables)}",
        f"Views: {len(report.views)}",
        f"Columns: {len(report.columns)}",
        f"Constraints: {len(report.constraints)}",
        f"Indexes: {len(report.indexes)}",
        f"Triggers: {len(report.triggers)}",
        "",
        "TABLES",
    ]
    lines.extend(f"- {item}" for item in report.tables)
    lines.append("")
    lines.append("CONSTRAINTS")
    lines.extend(
        f"- {item.schema_name}.{item.table_name}.{item.constraint_name}: {item.definition}"
        for item in report.constraints
    )
    return "\n".join(lines)


def format_production_report(report: ProductionNameQualificationReport) -> str:
    lines = [
        "REFERENCE REGISTRY PRODUCTION AUTHORING QUALIFICATION",
        "=" * 72,
        f"Qualification ID: {report.qualification_id}",
        f"Canonical ID: {report.canonical_name_id}",
        f"Canonical value: {report.canonical_value}",
        f"Search value: {report.search_value}",
        f"Name kind: {report.name_kind}",
        f"Runtime: {report.runtime_mode}",
        f"First outcome: {report.first_outcome}",
        f"Duplicate outcome: {report.duplicate_outcome}",
        f"Production matches: {report.production_match_count}",
        f"Simulation matches: {report.simulation_match_count}",
        f"Passed: {report.passed}",
        "",
        "FINDINGS",
    ]
    lines.extend(f"- [{item.status.upper()}] {item.code}: {item.message}" for item in report.findings)
    return "\n".join(lines)


__all__ = ["format_json", "format_schema_report", "format_production_report"]
