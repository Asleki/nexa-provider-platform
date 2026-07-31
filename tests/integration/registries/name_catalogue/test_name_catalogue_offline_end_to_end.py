from datetime import datetime,timezone
from registries.name_cache import *
from registries.name_sync import *
from registries.name_integrations import *
from registries.names.canonical_name import CanonicalName
from registries.names.name_kind import NameKind
from registries.names.name_metadata import NameMetadata
from registries.names.name_search_query import NameSearchQuery

def test_offline_catalogue_end_to_end():
    now=lambda:datetime(2026,7,31,tzinfo=timezone.utc)
    cache=MemoryNameCacheRepository("simulation"); receipts=MemoryNameSyncReceiptRepository(); sync=NameSyncService(cache,receipts,now,lambda:"receipt-1"); api=NameCatalogueApi(cache,sync,receipts)
    record=CanonicalName("name:alex","Alex",NameKind.FIRST_NAME,NameMetadata(runtime_mode="simulation")); entry=NameCacheEntry(record,"1",now())
    receipt=api.apply_snapshot(NameSyncRequest("request-1",NameSyncOperation.APPLY_SNAPSHOT,"simulation",now()),NameCatalogueSnapshot("snapshot-1","simulation","catalogue-1","checkpoint-1",now(),(entry,))).payload
    assert receipt.ending_checkpoint=="checkpoint-1"
    assert api.search(NameSearchQuery(text="Al",runtime_mode="simulation")).payload["total"]==1
    assert api.get_receipt("request-1").ok
