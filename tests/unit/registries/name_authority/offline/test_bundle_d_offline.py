from registries.name_authority.offline import *
from registries.name_authority.read_models import MemoryNameAuthorityReadRepository,NameAuthorityReadModel
from registries.name_authority.authority import AuthorityNameComposition,AuthorityNameStatus
from registries.name_authority.application import ApplicationPrincipal,ApplicationRequestContext

def ctx(runtime="simulation"):
    return ApplicationRequestContext("req","corr",runtime,"testing",ApplicationPrincipal("actor","operator","device",frozenset(),frozenset({runtime})))
def test_partition_and_policy_contracts():
    assert policy_for("approve_manual") is OfflineOperationPolicy.ONLINE_REQUIRED
    p=OfflinePartition("a","d","production")
    d=NameAuthorityOfflineDraft("draft:1",p,{"name":"Makomeri"})
    repo=MemoryOfflineRepository(); repo.save_draft(d)
    assert repo.drafts[("a","d","production","draft:1")]==d

def test_snapshot_is_scoped_checksummed_and_runtime_safe():
    r=MemoryNameAuthorityReadRepository()
    r.upsert(NameAuthorityReadModel("nameauth:1","simulation",AuthorityNameComposition.FIRST_SURNAME,"A B","a b",("n1","n2"),("A","B"),"simulation",AuthorityNameStatus.ACTIVE))
    service=NameAuthorityOfflineService(r,MemoryOfflineRepository())
    snapshot=service.create_snapshot(ctx(),{"limit":25})
    assert snapshot["manifest"].runtime_mode=="simulation"
    assert snapshot["manifest"].checksum==snapshot["pages"][0].page_checksum

def test_sync_receipt_is_idempotent_and_checksum_conflicts_are_rejected():
    repo=MemoryOfflineRepository(); service=NameAuthorityOfflineService(MemoryNameAuthorityReadRepository(),repo)
    r=NameAuthoritySyncReceipt("receipt:1","req","dev","actor","simulation","snap",1,0,0,"abc")
    assert service.acknowledge(r)==r and service.acknowledge(r)==r
    bad=NameAuthoritySyncReceipt("receipt:1","req","dev","actor","simulation","snap",1,0,0,"different")
    try: service.acknowledge(bad)
    except ValueError: pass
    else: raise AssertionError("expected checksum conflict")
