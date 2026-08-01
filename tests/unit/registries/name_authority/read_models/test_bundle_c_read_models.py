from registries.names import CanonicalName,NameKind,NameMetadata
from registries.name_authority.authority import *
from registries.name_authority.read_models import *

def atom(i,v,k,mode="simulation"): return CanonicalName(i,v,k,NameMetadata(runtime_mode=mode))
def rec(first,surname,seq):
    return AuthorityNameBuilder().build("first_surname",(first,surname),("first_name","surname"),runtime_mode="simulation",metadata={"generation":{"batch_id":"b1","sequence":seq,"family":"novegeo_native_two_part"}})

def test_projection_search_cursor_and_runtime_isolation():
    repo=MemoryNameAuthorityReadRepository(); p=NameAuthorityReadModelProjector()
    records=[rec(atom("f1","Ava",NameKind.FIRST_NAME),atom("s1","Dube",NameKind.SURNAME),1),rec(atom("f2","Ava",NameKind.FIRST_NAME),atom("s2","Moyo",NameKind.SURNAME),2)]
    cp=p.rebuild(records,repo,"simulation"); assert cp.projected_count==2
    page1=repo.search(NameAuthoritySearchQuery("simulation",text="ava",limit=1)); assert page1.has_more and page1.next_cursor
    page2=repo.search(NameAuthoritySearchQuery("simulation",text="ava",limit=1,cursor=page1.next_cursor)); assert len(page2.items)==1 and page1.items[0].authority_name_id!=page2.items[0].authority_name_id
    assert repo.search(NameAuthoritySearchQuery("production",text="ava")).items==()

def test_cursor_tampering_and_statistics():
    import pytest
    with pytest.raises(ValueError): NameAuthoritySearchCursor.decode("not-a-cursor")
    repo=MemoryNameAuthorityReadRepository(); p=NameAuthorityReadModelProjector(); p.rebuild([rec(atom("f1","Ava",NameKind.FIRST_NAME),atom("s1","Dube",NameKind.SURNAME),1)],repo,"simulation")
    stats=repo.statistics("simulation"); assert stats.total==1 and stats.by_generation_family["novegeo_native_two_part"]==1
