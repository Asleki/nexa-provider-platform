import pytest
from registries.names import CanonicalName,MemoryNameRepository,NameKind,NameMetadata,NameSearchQuery,NameSearchService,NameStatus

def test_search_filters_prefix_exact_kind_status_runtime_and_pages():
    repo=MemoryNameRepository()
    repo.add(CanonicalName("1","Tariro",NameKind.FIRST_NAME))
    repo.add(CanonicalName("2","Tawanda",NameKind.FIRST_NAME))
    repo.add(CanonicalName("3","Tariro",NameKind.SURNAME))
    repo.add(CanonicalName("4","Tapiwa",NameKind.FIRST_NAME,NameMetadata(status=NameStatus.DEPRECATED)))
    service=NameSearchService(repo)
    r=service.search(NameSearchQuery("Ta",name_kind=NameKind.FIRST_NAME,limit=1))
    assert r.total==2 and len(r.records)==1
    exact=service.search(NameSearchQuery("tariro",name_kind=NameKind.FIRST_NAME,exact=True))
    assert [x.name_id for x in exact.records]==["1"]
    all_status=service.search(NameSearchQuery("Ta",status=None))
    assert all_status.total==4

def test_search_service_requires_contract():
    with pytest.raises(TypeError): NameSearchService(object())
