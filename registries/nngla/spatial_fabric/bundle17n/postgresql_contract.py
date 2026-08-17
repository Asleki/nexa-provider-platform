"""PostgreSQL durability contract for runtime command execution."""
from ._shared import SCHEMA_PATH
def load_schema17n_sql(): return SCHEMA_PATH.read_text(encoding="utf-8")
def qualify_schema17n_sql(sql: str) -> tuple[str,...]:
    n=sql.lower(); compact="".join(n.split()); findings=[]
    for token in (
        "create table geography.nngla_runtime_command_receipt",
        "create table geography.nngla_runtime_bulk_operation_receipt",
        "create or replace function geography.nngla_claim_runtime_command",
        "request_fingerprint",
        "idempotency_key",
        "for update",
        "runtime_mode",
        "effect_scope",
        "event_id",
        "audit_id",
    ):
        if token not in n: findings.append("missing-sql:"+token)
    if "unique(runtime_mode,command_code,idempotency_key)" not in compact:
        findings.append("missing-sql:runtime-command-idempotency-unique")
    for bad in ("nexaecosystem.com","localhost","namecheap","password"):
        if bad in n: findings.append("forbidden-coupling:"+bad)
    for old in ("nngla_spatial_feature","nngla_geometry_version","nngla_road","nngla_address","nngla_parcel","nngla_title"):
        if f"alter table geography.{old}" in n: findings.append("locked-table-alteration:"+old)
    return tuple(findings)
__all__=["load_schema17n_sql","qualify_schema17n_sql"]
