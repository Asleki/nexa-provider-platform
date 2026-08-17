"""Bundle 17H additive PostgreSQL contract for atomic scoped address allocation."""
from __future__ import annotations

from pathlib import Path
from ._shared import ROOT

SCHEMA17H_SQL = ROOT / "database" / "schemas" / "nngla_smart_addressing_sites.sql"
REQUIRED_TABLES = (
    "geography.nngla_road_segment",
    "geography.nngla_road_frontage",
    "geography.nngla_address_series",
    "geography.nngla_address_number_reservation",
    "geography.nngla_structure_site_reference",
    "geography.nngla_site_address_assignment",
)


def load_schema17h_sql(path: Path = SCHEMA17H_SQL) -> str:
    return Path(path).read_text(encoding="utf-8")


def qualify_schema17h_sql(sql: str) -> tuple[str, ...]:
    n = sql.lower(); findings = []
    for table in REQUIRED_TABLES:
        if f"create table {table}" not in n:
            findings.append(f"missing:{table}")
    required = (
        "unique (series_id, normalized_number_key)",
        "unique (reserved_address_id)",
        "idempotency_key",
        "for update",
        "nngla_reserve_address_number",
        "sequence_step",
        "next_sequence",
        "road_id",
        "site_id",
        "nngla_address_id_sequence",
        "nextval",
    )
    for token in required:
        if token not in n:
            findings.append(f"missing-sql:{token}")
    for forbidden in ("street_id", "nexaecosystem.com", "localhost", "namecheap"):
        if forbidden in n:
            findings.append(f"forbidden-coupling:{forbidden}")
    if "alter table geography.nngla_address" in n or "alter table geography.nngla_road" in n:
        findings.append("locked-base-table-destructive-alteration")
    return tuple(findings)


__all__ = ["SCHEMA17H_SQL", "REQUIRED_TABLES", "load_schema17h_sql", "qualify_schema17h_sql"]
