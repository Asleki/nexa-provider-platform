from registries.names import MemoryNameRepository,CanonicalName,NameMetadata,NameKind
from registries.names.name_sex_usage import NameSexUsage
from registries.name_authority.repositories.memory import MemoryManualNameCandidateRepository,MemoryNameAuthorityRepository
from registries.name_authority.manual import ProductionManualNameService,ProductionManualNameRequest,ActorContext
from registries.name_authority.authority import NameAuthorityService,AuthorityNameComposition,AuthorityComponentRole
from registries.name_authority.read_models import MemoryNameAuthorityReadRepository,NameAuthorityReadModelProjector,NameAuthoritySearchQuery
from registries.name_authority.application import *
from registries.name_authority.application.permissions import *
from registries.name_authority.offline import *

def mkctx(actor,perms,key=None,runtime="production"):
    p=ApplicationPrincipal(actor,"operator","device:integration",frozenset(perms),frozenset({runtime}))
    return ApplicationRequestContext("request:"+actor,"correlation:bundle-d",runtime,"testing",p,key)
def test_bundle_d_zero_person_application_and_offline_flow():
    names=MemoryNameRepository(); candidates=MemoryManualNameCandidateRepository(); authrepo=MemoryNameAuthorityRepository(); readrepo=MemoryNameAuthorityReadRepository(); offrepo=MemoryOfflineRepository()
    manual=ProductionManualNameService(names,candidates); authority=NameAuthorityService(authrepo); offline=NameAuthorityOfflineService(readrepo,offrepo); receipts=MemoryApplicationReceiptRepository()
    service=NameAuthorityApplicationService(readrepo,names,candidates,manual,authority,receipts,offline); api=NameAuthorityApplicationApi(service)
    request=ProductionManualNameRequest("manual:bundle-d","operation:bundle-d","Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE,ActorContext("operator:1","operator"))
    submitted=api.execute(NameAuthorityOperation.SUBMIT_MANUAL,mkctx("operator:1",{MANUAL_CREATE},"idem:1"),request=request)
    approved=api.execute(NameAuthorityOperation.APPROVE_MANUAL,mkctx("approver:1",{MANUAL_APPROVE},"idem:2"),candidate_id=submitted.data[0].candidate_id)
    surname=CanonicalName("name:kobe","Kobe",NameKind.SURNAME,NameMetadata(runtime_mode="production")); names.add(surname)
    composed=api.execute(NameAuthorityOperation.COMPOSE,mkctx("operator:1",{COMPOSE},"idem:3"),composition=AuthorityNameComposition.FIRST_SURNAME,atomic_name_ids=(approved.data.canonical_name_id,surname.name_id),roles=(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME))
    readrepo.upsert(NameAuthorityReadModelProjector().project(composed.data))
    found=api.execute(NameAuthorityOperation.SEARCH,mkctx("reader:1",{SEARCH}),query=NameAuthoritySearchQuery(runtime_mode="production",text="Makomeri"))
    snap=api.execute(NameAuthorityOperation.SNAPSHOT,mkctx("reader:1",{SNAPSHOT_READ}),scope={"limit":25})
    assert found.ok and snap.ok and found.data.items[0].authority_name_id==composed.data.authority_name_id
    payload=str(found.data)+str(snap.data)
    for forbidden in ("person_id","citizen_id","birth_id","household_id","NPP_POSTGRES_PASSWORD"):
        assert forbidden not in payload
