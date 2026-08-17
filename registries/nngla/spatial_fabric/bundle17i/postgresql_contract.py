"""Bundle 17I additive PostgreSQL contract for title-reference reservation and legal-link candidates."""
from __future__ import annotations
from pathlib import Path
from ._shared import ROOT

SCHEMA17I_SQL = ROOT / "database" / "schemas" / "nngla_title_reservations_state_land_candidates.sql"
REQUIRED_TABLES = (
    "geography.nngla_title_number_series",
    "geography.nngla_title_reference_reservation",
    "geography.nngla_title_issuance_candidate",
    "geography.nngla_state_land_candidate_record",
)


def load_schema17i_sql(path: Path = SCHEMA17I_SQL) -> str:
    return Path(path).read_text(encoding="utf-8")


def qualify_schema17i_sql(sql: str) -> tuple[str, ...]:
    n = sql.lower(); findings = []
    for table in REQUIRED_TABLES:
        if f"create table {table}" not in n: findings.append(f"missing:{table}")
    for token in (
        "nngla_reserve_title_reference", "for update", "unique (reserved_title_id)", "idempotency_key",
        "legal_title_exists", "parcel_id text", "holder_reference text", "state_land_category_code",
        "v_reserved_title_id", "next_sequence",
    ):
        if token not in n: findings.append(f"missing-sql:{token}")
    if "parcel_id text not null" in n.split("create table geography.nngla_title_reference_reservation",1)[1].split(");",1)[0]:
        findings.append("title-reservation-must-allow-null-parcel")
    if "holder_reference text not null" in n.split("create table geography.nngla_title_reference_reservation",1)[1].split(");",1)[0]:
        findings.append("title-reservation-must-allow-null-holder")
    for forbidden in ("nexaecosystem.com", "localhost", "namecheap"):
        if forbidden in n: findings.append(f"forbidden-coupling:{forbidden}")
    if "alter table geography.nngla_title" in n or "alter table geography.nngla_state_land" in n:
        findings.append("locked-base-table-destructive-alteration")
    return tuple(findings)


__all__ = ["SCHEMA17I_SQL", "REQUIRED_TABLES", "load_schema17i_sql", "qualify_schema17i_sql"]
