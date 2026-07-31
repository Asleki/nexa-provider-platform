from datetime import datetime,timezone
import pytest
from registries.name_cache import *
from registries.names.canonical_name import CanonicalName
from registries.names.name_kind import NameKind
from registries.names.name_metadata import NameMetadata
from registries.names.name_search_query import NameSearchQuery

def rec(i,v,mode="simulation"):
    return CanonicalName(i,v,NameKind.FIRST_NAME,NameMetadata(runtime_mode=mode))
def entry(i,v,mode="simulation"):
    return NameCacheEntry(rec(i,v,mode),"1",datetime(2026,1,1,tzinfo=timezone.utc))
def test_cache_snapshot_search_and_runtime_isolation():
    cache=MemoryNameCacheRepository("simulation")
    state=NameCacheState("simulation",NameCacheStatus.READY,1,"v1","cp1",2,datetime.now(timezone.utc))
    cache.replace_snapshot((entry("n1","Alex"),entry("n2","Alice")),state)
    assert cache.search(NameSearchQuery(text="Al",runtime_mode="simulation")).total==2
    assert cache.search(NameSearchQuery(text="Al",runtime_mode="production")).total==0
    assert cache.get("n1").record.canonical_value=="Alex"
def test_snapshot_validation_is_failure_safe():
    cache=MemoryNameCacheRepository("simulation")
    with pytest.raises(ValueError):
        cache.replace_snapshot((entry("n1","Alex","production"),),NameCacheState("simulation",NameCacheStatus.READY,entry_count=1))
    assert cache.get_state().entry_count==0
