"""Human and JSON formatting for catalogue-plan execution."""
from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime

def _default(v):
    if isinstance(v,datetime): return v.isoformat()
    if hasattr(v,"value"): return v.value
    if isinstance(v,tuple): return list(v)
    raise TypeError

def format_payload(value): return json.dumps(asdict(value) if hasattr(value,"__dataclass_fields__") else value,indent=2,sort_keys=True,ensure_ascii=False,default=_default)

def format_preview(p):
    lines=["CATALOGUE PLAN PREVIEW","="*72,f"Plan: {p.plan_id}",f"Runtime: {p.runtime_mode}",f"Sample size per step: {p.sample_size_per_step}",f"Random seed: {p.random_seed}",f"Expected candidates: {p.expected_candidate_count}",f"Plan fingerprint: {p.plan_fingerprint}","", "STEPS"]
    for s in p.steps: lines.append(f"- {s.step_id}: {s.target_kind}, source rows={s.source_row_count}, selected={len(s.selected_source_record_ids)}")
    lines.extend(["",f"Confirmation: {p.confirmation_token}","Database writes performed: 0"]); return "\n".join(lines)

def format_receipt(r):
    lines=["CATALOGUE PLAN EXECUTION RECEIPT","="*72,f"Execution ID: {r.execution_id}",f"Plan: {r.plan_id}",f"Runtime: {r.runtime_mode}",f"Status: {r.status}",f"Selected: {r.selected_count}",f"Imported: {r.imported_count}",f"Already existing: {r.existing_count}",f"Failed: {r.failed_count}","", "STEPS"]
    for s in r.steps: lines.append(f"- {s.step_id}: imported={s.imported_count}, existing={s.existing_count}, profiles-created={s.profiles_created}, failed={s.failed_count}")
    return "\n".join(lines)
__all__=["format_payload","format_preview","format_receipt"]
