from datetime import datetime,timezone,timedelta
from registries.name_cache import *
from registries.name_sync import *
from registries.names.canonical_name import CanonicalName
from registries.names.name_kind import NameKind
from registries.names.name_metadata import NameMetadata

def clock(): return datetime(2026,7,31,tzinfo=timezone.utc)
def e(i,v): return NameCacheEntry(CanonicalName(i,v,NameKind.FIRST_NAME,NameMetadata(runtime_mode="simulation")),"1",clock())
def service():
    cache=MemoryNameCacheRepository("simulation"); receipts=MemoryNameSyncReceiptRepository(); ids=iter(["r1","r2","r3"])
    return cache,receipts,NameSyncService(cache,receipts,clock,lambda:next(ids))
def test_snapshot_application_and_idempotency():
    cache,receipts,svc=service(); snap=NameCatalogueSnapshot("s1","simulation","v1","cp1",clock(),(e("n1","Alex"),))
    req=NameSyncRequest("q1",NameSyncOperation.APPLY_SNAPSHOT,"simulation",clock())
    first=svc.apply_snapshot(req,snap); second=svc.apply_snapshot(req,snap)
    assert first is second and first.accepted_count==1 and cache.get_state().checkpoint=="cp1"
def test_incremental_upsert_remove_and_checkpoint():
    cache,receipts,svc=service(); svc.apply_snapshot(NameSyncRequest("q1",NameSyncOperation.APPLY_SNAPSHOT,"simulation",clock()),NameCatalogueSnapshot("s1","simulation","v1","cp1",clock(),(e("n1","Alex"),)))
    changes=(NameCatalogueChange("c1",NameChangeType.UPSERT,"n2","1",e("n2","Alice")),NameCatalogueChange("c2",NameChangeType.REMOVE,"n1","2"))
    receipt=svc.apply_change_set(NameSyncRequest("q2",NameSyncOperation.APPLY_CHANGE_SET,"simulation",clock()),NameCatalogueChangeSet("cs1","simulation","cp1","cp2","v2",clock(),changes))
    assert receipt.accepted_count==2 and cache.get_state().checkpoint=="cp2" and cache.get_state().entry_count==1

def test_checkpoint_mismatch_rejected_without_state_change():
    cache,receipts,svc=service(); svc.apply_snapshot(NameSyncRequest("q1",NameSyncOperation.APPLY_SNAPSHOT,"simulation",clock()),NameCatalogueSnapshot("s1","simulation","v1","cp1",clock(),()))
    receipt=svc.apply_change_set(NameSyncRequest("q2",NameSyncOperation.APPLY_CHANGE_SET,"simulation",clock()),NameCatalogueChangeSet("cs1","simulation","wrong","cp2","v2",clock(),()))
    assert receipt.status is NameSyncStatus.REJECTED and cache.get_state().checkpoint=="cp1"
