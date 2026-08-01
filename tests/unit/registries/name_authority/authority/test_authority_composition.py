import pytest
from registries.name_authority.authority import *
from registries.name_authority.repositories import MemoryNameAuthorityRepository
from registries.names import CanonicalName,NameKind,NameMetadata,NameStatus

def n(i,v,k,r="production",s=NameStatus.ACTIVE): return CanonicalName(i,v,k,NameMetadata(runtime_mode=r,status=s))
def test_builds_ordered_three_part_authority_identity_and_deduplicates():
 names=(n("name:m","Makomeri",NameKind.FIRST_NAME),n("name:i","Ignatius",NameKind.MIDDLE_NAME),n("name:k","Kobe",NameKind.SURNAME))
 b=AuthorityNameBuilder(); r=b.build(AuthorityNameComposition.FIRST_MIDDLE_SURNAME,names,(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.MIDDLE_NAME,AuthorityComponentRole.SURNAME),actor_id="actor:1")
 assert r.display_name=="Makomeri Ignatius Kobe" and [c.position for c in r.components]==[1,2,3]
 repo=MemoryNameAuthorityRepository(); assert repo.create_or_get(r) is repo.create_or_get(r)
def test_rejects_wrong_roles_mixed_runtime_and_inactive_components():
 b=AuthorityNameBuilder()
 with pytest.raises(ValueError): b.build("first_surname",(n("name:a","A",NameKind.FIRST_NAME),n("name:b","B",NameKind.MIDDLE_NAME)),("first_name","surname"))
 with pytest.raises(ValueError): b.build("first_surname",(n("name:a","A",NameKind.FIRST_NAME),n("name:b","B",NameKind.SURNAME,"simulation")),("first_name","surname"))
 with pytest.raises(ValueError): b.build("single_name",(n("name:x","X",NameKind.FIRST_NAME,s=NameStatus.DEPRECATED),),("single_name",))
def test_same_display_can_have_distinct_semantic_composition_keys():
 b=AuthorityNameBuilder(); single=b.build("single_name",(n("name:jp","Jean Pierre",NameKind.FIRST_NAME),),("single_name",))
 pair=b.build("first_surname",(n("name:j","Jean",NameKind.FIRST_NAME),n("name:p","Pierre",NameKind.SURNAME)),("first_name","surname"))
 assert single.display_name==pair.display_name and single.composition_key!=pair.composition_key
