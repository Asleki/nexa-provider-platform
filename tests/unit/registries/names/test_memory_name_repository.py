from dataclasses import replace
import pytest
from registries.names import CanonicalName,MemoryNameRepository,NameIdentityConflictError,NameKind,NameMetadata,NameNotFoundError,NameStatus

def test_memory_repository_crud_and_deterministic_listing():
    repo=MemoryNameRepository()
    b=CanonicalName("id:b","Busi",NameKind.FIRST_NAME)
    a=CanonicalName("id:a","Amina",NameKind.FIRST_NAME)
    repo.add(b); repo.add(a)
    assert repo.count()==2 and repo.exists("id:a") and repo.get("id:a")==a
    assert [x.name_id for x in repo.list_all()]==["id:a","id:b"]
    updated=replace(a,metadata=replace(a.metadata,status=NameStatus.DEPRECATED))
    assert repo.replace(updated).metadata.status is NameStatus.DEPRECATED
    with pytest.raises(NameNotFoundError): repo.get("missing")

def test_memory_repository_prevents_semantic_duplicates_but_separates_runtime():
    repo=MemoryNameRepository(); repo.add(CanonicalName("id:1","Tariro",NameKind.FIRST_NAME))
    with pytest.raises(NameIdentityConflictError): repo.add(CanonicalName("id:2"," TARIRO ",NameKind.FIRST_NAME))
    prod=CanonicalName("id:3","Tariro",NameKind.FIRST_NAME,NameMetadata(runtime_mode="production"))
    repo.add(prod); assert repo.count()==2
