"""Atomic reference authoring service."""
from __future__ import annotations
from uuid import uuid4
from .contracts import ReferenceRecord,ReferenceType
class AtomicReferenceCodeAllocator:
    PREFIX={ReferenceType.TRIBE:"trb",ReferenceType.LANGUAGE:"lng",ReferenceType.ORIGIN:"org"}
    def __init__(self,next_number): self._next=next_number
    def allocate(self,reference_type):
        t=ReferenceType.parse(reference_type); return f"{self.PREFIX[t]}_{int(self._next(t)):03d}"
class ReferenceAuthoringService:
    def __init__(self,repository,allocator): self.repository=repository; self.allocator=allocator
    def author(self,request):
        search=request.canonical_label.casefold()
        existing=self.repository.find(request.reference_type.value,request.runtime_mode,search)
        if existing: return existing,False
        code=request.requested_code or self.allocator.allocate(request.reference_type)
        record=ReferenceRecord(reference_id=f"{request.reference_type.value}:{uuid4().hex}",reference_code=code,reference_type=request.reference_type,canonical_label=request.canonical_label,runtime_mode=request.runtime_mode,source_reference=request.source_reference,origin_type=request.origin_type,native_label=request.native_label,attributes=request.attributes,created_by_actor_id=request.submitter_actor_id,approved_by_actor_id=request.approver_actor_id)
        return self.repository.add(record),True
__all__=["AtomicReferenceCodeAllocator","ReferenceAuthoringService"]
