"""Human-led production name introduction services."""
from __future__ import annotations
import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from registries.names import CanonicalName,NameMetadata,NameSearchQuery,NameStatus
from registries.names.name_repository_errors import NameIdentityConflictError
from .contracts import *

class ManualNameValidator:
    def validate(self,request:ProductionManualNameRequest)->ManualNameValidation:
        findings=[]
        if request.requested_name_kind.value in ("first_name","middle_name") and request.sex_usage.value=="unspecified": findings.append("NAME_SEX_USAGE_REVIEW_REQUIRED")
        if any(unic in request.raw_name_value for unic in ("\u202e","\u202d","\u2066","\u2067","\u2068","\u2069")): findings.append("NAME_BIDI_CONTROL_REJECTED")
        valid="NAME_BIDI_CONTROL_REJECTED" not in findings
        return ManualNameValidation(valid,bool(findings),tuple(findings))

class ProductionManualNameService:
    def __init__(self,name_repository,candidate_repository,validator:ManualNameValidator|None=None): self.names=name_repository; self.candidates=candidate_repository; self.validator=validator or ManualNameValidator()
    @staticmethod
    def candidate_id(request): return "manualcandidate:"+hashlib.sha256(f"{request.request_id}|{request.requested_name_kind.value}|{request.raw_name_value}".encode()).hexdigest()[:32]
    def submit(self,request):
        result=self.validator.validate(request); status=ManualNameCandidateStatus.VALIDATED if result.is_valid and not result.requires_review else (ManualNameCandidateStatus.QUARANTINED if result.is_valid else ManualNameCandidateStatus.REJECTED)
        candidate=ManualNameCandidate(self.candidate_id(request),request,status)
        return self.candidates.add(candidate),result
    def approve(self,candidate_id:str,approver:ActorContext,reason:str="approved"):
        candidate=self.candidates.get(candidate_id)
        if candidate.status not in (ManualNameCandidateStatus.VALIDATED,ManualNameCandidateStatus.QUARANTINED): raise ValueError("candidate is not approval-eligible.")
        query=NameSearchQuery(text=candidate.request.raw_name_value,name_kind=candidate.request.requested_name_kind,runtime_mode="production",exact=True,limit=2)
        found=self.names.search(query).records
        if found:
            record=found[0]; outcome=ManualNameApprovalOutcome.REUSED_EXISTING_CANONICAL_NAME
        else:
            name_id="name:manual:"+hashlib.sha256((candidate.request.requested_name_kind.value+"|"+candidate.search_value).encode()).hexdigest()[:32]
            attrs={"manual":{"request_id":candidate.request.request_id,"candidate_id":candidate.candidate_id,"submitted_by":candidate.request.actor.actor_id,"approved_by":approver.actor_id,"origin":candidate.request.origin.__dict__ if hasattr(candidate.request.origin,'__dict__') else {"knowledge_state":candidate.request.origin.knowledge_state.value,"binding_state":candidate.request.origin.binding_state.value,"label":candidate.request.origin.label,"reference_id":candidate.request.origin.reference_id}}}
            md=NameMetadata(status=NameStatus.ACTIVE,runtime_mode="production",source_reference="manual.production",script_code=candidate.request.script_code,attributes=attrs)
            record=CanonicalName(name_id,candidate.request.raw_name_value,candidate.request.requested_name_kind,md)
            try: self.names.add(record); outcome=ManualNameApprovalOutcome.CREATED_NEW_CANONICAL_NAME
            except NameIdentityConflictError:
                record=self.names.search(query).records[0]; outcome=ManualNameApprovalOutcome.REUSED_EXISTING_CANONICAL_NAME
        updated=replace(candidate,status=ManualNameCandidateStatus.APPROVED,canonical_name_id=record.name_id,reviewed_by_actor_id=approver.actor_id,reviewed_at=datetime.now(timezone.utc),decision_reason=reason)
        self.candidates.replace(updated); return ManualNameApprovalResult(updated,outcome,record.name_id)
