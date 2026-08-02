"""Sanitized human and JSON formatting."""
from __future__ import annotations
import json
from dataclasses import asdict,is_dataclass
from datetime import datetime

def _clean(v):
    if is_dataclass(v): return {k:_clean(x) for k,x in asdict(v).items()}
    if isinstance(v,(tuple,list)): return [_clean(x) for x in v]
    if isinstance(v,datetime): return v.isoformat()
    if isinstance(v,dict): return {k:_clean(x) for k,x in v.items()}
    return v
def format_json(value): return json.dumps(_clean(value),sort_keys=True,indent=2)
def format_status(s):
    return "\n".join([
        f"Ledger state: {s.ledger_state}",
        f"Repository migrations: {s.repository_migrations}",
        f"Applied migrations: {s.applied_migrations}",
        f"Pending migrations: {s.pending_migrations}",
        f"Failed migrations: {s.failed_migrations}",
        f"Started migrations: {s.started_migrations}",
        f"Checksum mismatches: {s.checksum_mismatches}",
        f"Unknown database migrations: {s.unknown_database_migrations}",
        f"Plan checksum: {s.plan_checksum}",
    ])
