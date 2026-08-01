import pytest
from registries.name_authority.manual import *
from registries.name_authority.repositories import MemoryManualNameCandidateRepository
from registries.names import MemoryNameRepository,NameKind
from registries.names.name_sex_usage import NameSexUsage

def actor(i="actor:1"): return ActorContext(i,"user")
def request(value="Makomeri",kind=NameKind.FIRST_NAME):
 return ProductionManualNameRequest("request:1","operation:1",value,kind,NameSexUsage.MALE,actor(),origin=ReferenceDeclaration(ReferenceKnowledgeState.DECLARED_NEW,ReferenceBindingState.UNRESOLVED,"Koberian"))
def test_reference_states_and_production_runtime_are_strict():
 d=ReferenceDeclaration(ReferenceKnowledgeState.DECLARED_NEW,ReferenceBindingState.UNRESOLVED,"Koberian"); assert d.reference_id is None
 with pytest.raises(ValueError): ProductionManualNameRequest("request:x","operation:x","X",NameKind.FIRST_NAME,NameSexUsage.MALE,actor(),runtime_mode="simulation")
def test_submit_and_approve_creates_then_reuses_canonical_name():
 names=MemoryNameRepository(); candidates=MemoryManualNameCandidateRepository(); service=ProductionManualNameService(names,candidates)
 c,v=service.submit(request()); assert v.is_valid and c.status is ManualNameCandidateStatus.VALIDATED
 result=service.approve(c.candidate_id,actor("actor:approver")); assert result.outcome is ManualNameApprovalOutcome.CREATED_NEW_CANONICAL_NAME and names.count()==1
 req2=ProductionManualNameRequest("request:2","operation:2","Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE,actor())
 c2,_=service.submit(req2); r2=service.approve(c2.candidate_id,actor("actor:approver")); assert r2.outcome is ManualNameApprovalOutcome.REUSED_EXISTING_CANONICAL_NAME and names.count()==1
def test_unspecified_given_name_is_quarantined_for_human_review():
 service=ProductionManualNameService(MemoryNameRepository(),MemoryManualNameCandidateRepository())
 req=ProductionManualNameRequest("request:3","operation:3","Ari",NameKind.FIRST_NAME,NameSexUsage.UNSPECIFIED,actor())
 c,v=service.submit(req); assert v.requires_review and c.status is ManualNameCandidateStatus.QUARANTINED
