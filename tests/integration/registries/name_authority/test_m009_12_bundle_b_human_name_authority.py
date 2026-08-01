from registries.name_authority.manual import *
from registries.name_authority.authority import *
from registries.name_authority.repositories import *
from registries.names import *
def test_human_introduces_three_atoms_then_creates_name_authority_without_person_or_citizen():
 names=MemoryNameRepository(); candidates=MemoryManualNameCandidateRepository(); manual=ProductionManualNameService(names,candidates); actor=ActorContext("actor:registrar","registrar")
 ids=[]
 for i,(value,kind,usage) in enumerate((("Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE),("Ignatius",NameKind.MIDDLE_NAME,NameSexUsage.MALE),("Kobe",NameKind.SURNAME,NameSexUsage.UNSPECIFIED)),1):
  req=ProductionManualNameRequest(f"request:{i}",f"operation:{i}",value,kind,usage,actor)
  c,_=manual.submit(req); ids.append(manual.approve(c.candidate_id,actor).canonical_name_id)
 atoms=tuple(names.get(i) for i in ids); authority=NameAuthorityService(MemoryNameAuthorityRepository()).create_or_get("first_middle_surname",atoms,("first_name","middle_name","surname"),actor_id=actor.actor_id)
 assert authority.display_name=="Makomeri Ignatius Kobe" and names.count()==3
 assert not hasattr(authority,"person_id") and not hasattr(authority,"citizen_id")
