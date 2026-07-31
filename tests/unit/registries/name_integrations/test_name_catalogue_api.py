from datetime import datetime,timezone
from registries.name_cache import *
from registries.name_sync import *
from registries.name_integrations import *
from registries.names.canonical_name import CanonicalName
from registries.names.name_kind import NameKind
from registries.names.name_metadata import NameMetadata
from registries.names.name_search_query import NameSearchQuery

def now(): return datetime(2026,7,31,tzinfo=timezone.utc)
def test_api_snapshot_search_and_privacy_view():
    cache=MemoryNameCacheRepository("simulation"); rr=MemoryNameSyncReceiptRepository(); sync=NameSyncService(cache,rr,now,lambda:"r1"); api=NameCatalogueApi(cache,sync,rr)
    record=CanonicalName("n1","Alex",NameKind.FIRST_NAME,NameMetadata(runtime_mode="simulation",attributes={"internal":"hidden"}))
    entry=NameCacheEntry(record,"1",now()); req=NameSyncRequest("q1",NameSyncOperation.APPLY_SNAPSHOT,"simulation",now()); snap=NameCatalogueSnapshot("s1","simulation","v1","cp1",now(),(entry,))
    assert api.apply_snapshot(req,snap).ok
    response=api.search(NameSearchQuery(text="Alex",runtime_mode="simulation"))
    assert response.ok and response.payload["records"][0].name_id=="n1"
    assert not hasattr(response.payload["records"][0],"attributes")
