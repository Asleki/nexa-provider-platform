"""P006.7.11.5/.6 fingerprint-bound, transactional NNGLA batch execution."""
from __future__ import annotations
from dataclasses import dataclass, replace
from hashlib import sha256
from collections import Counter

from .plans import get_plan, PlanPurpose
from .preview import PreviewService, TargetStateSnapshot
from .selectors import Selector, select_records
from .source_catalogue import load_source
from .qualification import QualificationOutcome
from .persistence import ExistingMapping, canonical_payload_sha256, stable_id, candidate_id
from .receipts import ExecutionReceipt, ExecutionItemReceipt, utc_now

class ExecutionError(RuntimeError): pass

@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    plan_id: str
    repository_revision: str
    submitter_actor_id: str
    approver_actor_id: str
    approved_fingerprint: str
    confirmation: str
    selector_override: Selector | None = None

    def __post_init__(self):
        if not self.submitter_actor_id or not self.approver_actor_id: raise ValueError("submitter and approver are required")
        if self.submitter_actor_id == self.approver_actor_id: raise ValueError("submitter and approver must differ")
        if len(self.approved_fingerprint) != 64: raise ValueError("approved_fingerprint must be SHA-256")


def confirmation_token(plan_id:str,database_name:str,fingerprint:str)->str:
    return f"RUN NNGLA PLAN {plan_id} {database_name} {fingerprint[:12]}"

class ExecutionService:
    def __init__(self, repository):
        self.repository=repository; self.previews=PreviewService()

    def _rerun_target(self, target:TargetStateSnapshot, plan_id:str, selector_override:Selector|None):
        plan=get_plan(plan_id); snapshot=load_source(plan.source_key); plan=plan.with_selector(selector_override) if selector_override else plan
        selected=select_records(snapshot.records,plan.selector)
        mapped=dict(target.crosswalks or {})
        reusable={mapped[r.source_id] for r in selected if r.source_id in mapped}
        return TargetStateSnapshot(target.database_name,target.environment_name,target.schema_capabilities,
            frozenset(set(target.occupied_canonical_ids)-reusable),mapped)

    def preview_for_execution(self,plan_id:str,*,selector_override=None,repository_revision="UNRESOLVED"):
        target=self._rerun_target(self.repository.target_snapshot(),plan_id,selector_override)
        preview=self.previews.preview(plan_id,selector_override=selector_override,target=target,repository_revision=repository_revision)
        foundation_ready="nngla_execution_foundation" in target.schema_capabilities
        if not foundation_ready:
            preview=replace(preview,schema_ready=False,execution_ready=False)
        return preview

    def run(self, request:ExecutionRequest)->ExecutionReceipt:
        preview=self.preview_for_execution(request.plan_id,selector_override=request.selector_override,repository_revision=request.repository_revision)
        if preview.fingerprint != request.approved_fingerprint: raise ExecutionError("approved preview fingerprint no longer matches current plan")
        expected=confirmation_token(request.plan_id,preview.database_name,preview.fingerprint)
        if request.confirmation != expected: raise ExecutionError("NNGLA execution confirmation token does not match")
        if not preview.schema_ready: raise ExecutionError("NNGLA schema prerequisite is not installed")
        if not preview.execution_ready: raise ExecutionError("NNGLA preview is not execution-ready")
        plan=get_plan(request.plan_id); snapshot=load_source(plan.source_key); plan=plan.with_selector(request.selector_override) if request.selector_override else plan
        selected=select_records(snapshot.records,plan.selector)
        started=utc_now(); items=[]; inserted=reused=quarantined=failed=0
        execution_id="nnglarun:"+sha256(f"{preview.fingerprint}|{started.isoformat()}".encode()).hexdigest()[:24]
        batch_id="ingest:nngla:"+sha256(preview.fingerprint.encode()).hexdigest()[:24]
        with self.repository.transaction():
            self.repository.register_source(snapshot.descriptor,snapshot.source_sha256,snapshot.byte_size,len(snapshot.records))
            self.repository.register_batch(batch_id,snapshot.descriptor,plan.runtime_mode,plan.effect_scope)
            by_source={q.source_id:q for q in preview.findings}
            proposed_iter=iter(preview.proposed_canonical_ids)
            proposed_by_source={q.source_id:q.proposed_canonical_id for q in preview.findings if q.proposed_canonical_id}
            for record in selected:
                q=by_source[record.source_id]
                staged_id=stable_id("staged:nngla:",f"{batch_id}|{record.source_id}")
                self.repository.stage(staged_id,record,snapshot.descriptor.domain_family,batch_id)
                if q.outcome in {QualificationOutcome.BLOCKED,QualificationOutcome.QUARANTINE,QualificationOutcome.REVIEW_REQUIRED}:
                    code=q.findings[0].code if q.findings else q.outcome.value
                    detail=q.findings[0].detail if q.findings else q.outcome.value
                    self.repository.quarantine_record(staged_id,record,code,detail); quarantined+=1
                    items.append(ExecutionItemReceipt(record.source_id,"QUARANTINED",detail={"code":code,"detail":detail})); continue
                canonical_id=proposed_by_source.get(record.source_id)
                payload_sha=canonical_payload_sha256(dict(record.payload))
                existing=self.repository.existing_mapping(record.source_id)
                if existing:
                    if existing.source_payload_sha256 != payload_sha: raise ExecutionError(f"SOURCE_ID_CONFLICT for {record.source_id}")
                    if canonical_id and existing.canonical_id != canonical_id: raise ExecutionError(f"CROSSWALK_CONFLICT for {record.source_id}")
                    reused+=1; items.append(ExecutionItemReceipt(record.source_id,"REUSED",existing.canonical_id,publication_ready=True)); continue
                if plan.purpose is PlanPurpose.SOVEREIGN_AUTHORITY:
                    canonical_id=None
                self.repository.persist_canonical(snapshot.descriptor,record,canonical_id,plan.runtime_mode)
                if canonical_id:
                    mapping=ExistingMapping(record.source_id,canonical_id,payload_sha)
                    try:
                        crosswalk_id=self.repository.persist_crosswalk(mapping,descriptor=snapshot.descriptor,candidate=candidate_id(record),runtime_mode=plan.runtime_mode,effect_scope=plan.effect_scope)
                    except TypeError:
                        self.repository.persist_crosswalk(mapping); crosswalk_id=stable_id("crosswalk:nngla:",f"{snapshot.descriptor.dataset_id}|{record.source_id}|{canonical_id}")
                    receipt_id=stable_id("canonicalization:nngla:",f"{crosswalk_id}|{payload_sha}")
                    self.repository.persist_canonicalization_receipt(receipt_id,crosswalk_id,staged_id,payload_sha,tuple(f.code for f in q.findings))
                    event_id=stable_id("nngla-event:",f"{execution_id}|{record.source_id}")
                    audit_id=stable_id("audit:",f"{execution_id}|{record.source_id}")
                else:
                    crosswalk_id=receipt_id=event_id=audit_id=None
                inserted+=1
                items.append(ExecutionItemReceipt(record.source_id,"INSERTED",canonical_id,crosswalk_id,receipt_id,event_id,audit_id,True))
            completed=utc_now(); status="EMPTY" if not selected else "REUSED" if inserted==0 and reused>0 and quarantined==0 else "APPLIED"
            receipt=ExecutionReceipt(execution_id,plan.plan_id,plan.version,preview.fingerprint,preview.database_name,preview.environment_name,plan.runtime_mode,request.repository_revision,snapshot.source_sha256,request.submitter_actor_id,request.approver_actor_id,len(selected),inserted,reused,quarantined,failed,status,started,completed,tuple(items))
            self.repository.persist_execution_receipt(receipt)
        return receipt

__all__=["ExecutionError","ExecutionRequest","ExecutionService","confirmation_token"]
