"""Additive P006.7.3/P006.7.4 PostgreSQL schema-extension contract."""
from pathlib import Path
SCHEMA15A_SQL = Path(__file__).resolve().parents[2] / "database" / "schemas" / "nngla_geographic_identity_places.sql"
REQUIRED_15A_TABLES = (
    "geography.nngla_geographic_name",
    "geography.nngla_name_assignment",
    "geography.nngla_place_reference",
    "geography.nngla_administrative_area",
)
def load_schema15a_sql(path: Path = SCHEMA15A_SQL) -> str:
    return Path(path).read_text(encoding="utf-8")
def qualify_schema15a_sql(sql: str) -> tuple[str, ...]:
    n=sql.lower(); findings=[]
    for table in REQUIRED_15A_TABLES:
        if f"create table {table}" not in n: findings.append(f"missing:{table}")
    for token in ("source_place_code", "name_id", "parent_source_record_id", "geometry_reference", "runtime_effect_scope"):
        if token not in n: findings.append(f"missing-column:{token}")
    if "migration_manifest" in n: findings.append("schema-extension-must-not-register-locked-migration-manifest")
    return tuple(findings)
__all__=["SCHEMA15A_SQL","REQUIRED_15A_TABLES","load_schema15a_sql","qualify_schema15a_sql"]
