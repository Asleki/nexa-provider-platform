"""Bundle 17N architecture qualification."""
from .command_catalogue import command_definitions
from .authorization import authorization_rows
from .validation import validation_rules
from .bulk import bulk_policies
from ._shared import IDEMPOTENCY_POLICY_PATH, csv_rows
from .postgresql_contract import load_schema17n_sql, qualify_schema17n_sql

REQUIRED_COMMANDS=frozenset({
    "RESERVE_PARCEL_REFERENCE","RECOGNIZE_PARCEL","SUBDIVIDE_PARCEL",
    "CREATE_ADDRESSABLE_SITE","ALLOCATE_ADDRESS","RESERVE_TITLE_REFERENCE",
    "ISSUE_TITLE","ASSOCIATE_GEOMETRY","SUPERSEDE_GEOMETRY",
    "RECOGNIZE_FEATURE","RESERVE_NAME","APPROVE_NAME",
})
def bundle17n_is_qualified() -> bool:
    defs=command_definitions(); codes={d.command_code for d in defs}; auth=authorization_rows()
    expected={(d.command_code,rt) for d in defs for rt in d.allowed_runtimes}
    actual={(r["command_code"],r["runtime_code"]) for r in auth if r["status"]=="ACTIVE"}
    idemp=csv_rows(IDEMPOTENCY_POLICY_PATH)
    create_site=next(d for d in defs if d.command_code=="CREATE_ADDRESSABLE_SITE")
    sovereign={d for d in defs if d.identity_allocation_policy in {"SOVEREIGN_ALLOCATOR","RESERVED_REFERENCE_ONLY","CHILD_ALLOCATOR"}}
    return (
        REQUIRED_COMMANDS <= codes
        and create_site.allowed_runtimes==frozenset({"simulation","production"})
        and all(d.allowed_runtimes==frozenset({"production"}) for d in sovereign)
        and actual==expected and len(actual)==len(auth)
        and len(validation_rules()) >= len(defs)
        and {"BULK_ATOMIC","BULK_ITEM_ATOMIC","BULK_PREVIEW"} <= {p["bulk_policy_code"] for p in bulk_policies()}
        and len(idemp)>=1
        and any(r["same_key_different_fingerprint_outcome"]=="REJECT_CONFLICT" for r in idemp)
        and qualify_schema17n_sql(load_schema17n_sql())==()
    )
__all__=["REQUIRED_COMMANDS","bundle17n_is_qualified"]
