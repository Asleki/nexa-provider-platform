"""Catalogue-plan execution orchestration."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from registries.name_authority.production_context import get_plan
from .contracts import CataloguePlanExecutionReceipt
class CataloguePlanExecutionService:
    def __init__(self,preview_service,step_executor,*,clock=lambda:datetime.now(timezone.utc)): self.previews=preview_service; self.steps=step_executor; self.clock=clock
    def run(self,request,*,database_name,environment,confirmation):
        if not request.submitter_actor_id or not request.approver_actor_id: raise ValueError("submitter and approver are required for execution.")
        preview=self.previews.preview(request,database_name=database_name,environment=environment)
        if confirmation!=preview.confirmation_token: raise ValueError("catalogue plan execution was not confirmed.")
        started=self.clock(); receipts=[]; plan=get_plan(request.plan_id)
        for step,step_preview in zip(plan.steps,preview.steps): receipts.append(self.steps.execute(step,request,step_preview))
        completed=self.clock(); status="passed" if all(x.failed_count==0 for x in receipts) else "failed"
        execution_id="catrun:"+hashlib.sha256(f"{preview.plan_fingerprint}|{started.isoformat()}".encode()).hexdigest()[:24]
        return CataloguePlanExecutionReceipt(execution_id,request.plan_id,request.runtime_mode,database_name,environment,request.repository_revision,preview.plan_fingerprint,started,completed,status,tuple(receipts))
__all__=["CataloguePlanExecutionService"]
