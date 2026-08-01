from registries.adapters.postgresql import PostgreSQLConnectionProvider
from registries.name_authority.postgresql import PostgreSQLManualNameCandidateRepository,PostgreSQLNameAuthorityRepository
from registries.name_authority.manual import *
from registries.name_authority.authority import *
from registries.names import CanonicalName,NameKind,NameMetadata
from registries.names.name_sex_usage import NameSexUsage
class Cursor:
 def __init__(self,fetchone=None,fetchall=()): self.one=fetchone; self.all=fetchall; self.executed=[]; self.rowcount=1
 def execute(self,s,p=()): self.executed.append((s,p))
 def fetchone(self): return self.one
 def fetchall(self): return self.all
class Conn:
 def __init__(self,cur): self.cur=cur; self.committed=False; self.rolled=False; self.closed=False
 def cursor(self): return self.cur
 def commit(self): self.committed=True
 def rollback(self): self.rolled=True
 def close(self): self.closed=True

def test_candidate_repository_inserts_controlled_json_and_commits():
 cur=Cursor(); conn=Conn(cur); repo=PostgreSQLManualNameCandidateRepository(PostgreSQLConnectionProvider(lambda:conn))
 req=ProductionManualNameRequest("request:1","operation:1","Makomeri",NameKind.FIRST_NAME,NameSexUsage.MALE,ActorContext("actor:1","user"))
 c=ManualNameCandidate("candidate:1",req); repo.add(c)
 assert "manual_name_candidate" in cur.executed[0][0] and conn.committed and conn.closed

def test_authority_repository_inserts_record_and_components_atomically():
 cur=Cursor(fetchone=None,fetchall=(("name:a","active","production"),("name:b","active","production"))); conn=Conn(cur)
 repo=PostgreSQLNameAuthorityRepository(PostgreSQLConnectionProvider(lambda:conn))
 a=CanonicalName("name:a","A",NameKind.FIRST_NAME,NameMetadata(runtime_mode="production")); b=CanonicalName("name:b","B",NameKind.SURNAME,NameMetadata(runtime_mode="production"))
 record=AuthorityNameBuilder().build("first_surname",(a,b),("first_name","surname"))
 repo.create_or_get(record)
 sql="\n".join(x[0] for x in cur.executed); assert "name_authority_record" in sql and sql.count("name_authority_component")==2 and conn.committed
