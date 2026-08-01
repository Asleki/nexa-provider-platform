from registries.names import MemoryNameRepository,CanonicalName,NameMetadata,NameKind
from registries.name_authority.repositories.memory import MemoryManualNameCandidateRepository,MemoryNameAuthorityRepository
from registries.name_authority.manual import ProductionManualNameService,ProductionManualNameRequest,ActorContext,ReferenceDeclaration
from registries.names.name_sex_usage import NameSexUsage
from registries.name_authority.authority import NameAuthorityService,AuthorityNameComposition,AuthorityComponentRole
from registries.name_authority.read_models import MemoryNameAuthorityReadRepository,NameAuthorityReadModelProjector,NameAuthoritySearchQuery
from registries.name_authority.application import *
from registries.name_authority.application.permissions import *
from registries.name_authority.offline import MemoryOfflineRepository,NameAuthorityOfflineService

def build_service():
    names=MemoryNameRepository(); candidates=MemoryManualNameCandidateRepository(); authorities=MemoryNameAuthorityRepository(); reads=MemoryNameAuthorityReadRepository(); receipts=MemoryApplicationReceiptRepository(); offline=NameAuthorityOfflineService(reads,MemoryOfflineRepository())
    manual=ProductionManualNameService(names,candidates); authority=NameAuthorityService(authorities)
    service=NameAuthorityApplicationService(reads,names,candidates,manual,authority,receipts,offline)
    return service,names,candidates,authorities,reads

def principal(actor,permissions,runtimes=("production",)):
    return ApplicationPrincipal(actor,"operator","device:1",frozenset(permissions),frozenset(runtimes))
def context(actor,permissions,key=None,runtime="production"):
    return ApplicationRequestContext("req:1","corr:1",runtime,"testing",principal(actor,permissions,(runtime,)),key)

def test_runtime_and_permission_isolation():
    s,*_=build_service(); c=context("a",{READ},runtime="production")
    response=s.search(c,NameAuthoritySearchQuery(runtime_mode="production"))
    assert not response.ok and response.error.code is ApplicationErrorCode.PERMISSION_DENIED

def test_manual_submission_is_idempotent_and_self_approval_is_blocked():
    s,names,candidates,_,_=build_service(); submit=context("submitter",{MANUAL_CREATE},"idem:submit")
    req=ProductionManualNameRequest("manual:req:1","manual:op:1","Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE,ActorContext("submitter","operator"),ReferenceDeclaration())
    one=s.submit_manual(submit,req); two=s.submit_manual(submit,req)
    assert one.ok and two.data[0].candidate_id==one.data[0].candidate_id
    approve=context("submitter",{MANUAL_APPROVE},"idem:approve")
    blocked=s.approve_manual(approve,one.data[0].candidate_id)
    assert not blocked.ok and blocked.error.code is ApplicationErrorCode.SELF_APPROVAL_PROHIBITED

def test_separate_approver_and_composition_and_search():
    s,names,candidates,authorities,reads=build_service()
    req=ProductionManualNameRequest("manual:req:2","manual:op:2","Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE,ActorContext("submitter","operator"))
    candidate=s.submit_manual(context("submitter",{MANUAL_CREATE},"idem:s2"),req).data[0]
    approved=s.approve_manual(context("approver",{MANUAL_APPROVE},"idem:a2"),candidate.candidate_id)
    assert approved.ok
    surname=CanonicalName("name:kobe","Kobe",NameKind.SURNAME,NameMetadata(runtime_mode="production")); names.add(surname)
    composed=s.compose(context("composer",{COMPOSE},"idem:c2"),AuthorityNameComposition.FIRST_SURNAME,(approved.data.canonical_name_id,surname.name_id),(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME))
    assert composed.ok and composed.data.display_name=="Makomeri Kobe"
    reads.upsert(NameAuthorityReadModelProjector().project(composed.data))
    result=s.search(context("reader",{SEARCH}),NameAuthoritySearchQuery(runtime_mode="production",text="Makomeri"))
    assert result.ok and result.data.items[0].display_name=="Makomeri Kobe"
