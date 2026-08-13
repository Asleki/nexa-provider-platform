"""P006.7.2.7 PostgreSQL/PostGIS schema-foundation contract.

The DDL is intentionally not registered in the locked six-migration manifest.
"""
from pathlib import Path

NNGLA_SCHEMA_SQL = Path(__file__).resolve().parents[2] / "database" / "schemas" / "nngla_spatial_foundation.sql"
REQUIRED_TABLES = (
    "geography.nngla_source_dataset",
    "geography.nngla_source_artifact",
    "geography.nngla_ingest_batch",
    "geography.nngla_staged_record",
    "geography.nngla_quarantine_record",
    "geography.nngla_spatial_feature",
    "geography.nngla_geometry_version",
    "geography.nngla_canonical_crosswalk",
    "geography.nngla_canonicalization_receipt",
)


def load_schema_sql(path: Path = NNGLA_SCHEMA_SQL) -> str:
    return Path(path).read_text(encoding="utf-8")


def qualify_schema_sql(sql: str) -> tuple[str, ...]:
    findings = []
    normalized = sql.lower()
    for table in REQUIRED_TABLES:
        if f"create table {table}" not in normalized:
            findings.append(f"missing:{table}")
    for required in ("create extension if not exists postgis", "geometry(geometry, 4326)", "st_isvalid", "st_srid", "using gist"):
        if required not in normalized:
            findings.append(f"missing-sql:{required}")
    if "migration_manifest" in normalized:
        findings.append("schema-foundation-must-not-register-locked-migration-manifest")
    return tuple(findings)


__all__ = ["NNGLA_SCHEMA_SQL", "REQUIRED_TABLES", "load_schema_sql", "qualify_schema_sql"]
