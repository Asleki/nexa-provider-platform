"""DB-API PostgreSQL implementation of the locked NameRepository contract."""
from __future__ import annotations
from registries.names import CanonicalName,NameRepository,NameSearchQuery,NameSearchResult,comparison_key
from registries.names.name_repository_errors import NameAlreadyExistsError,NameIdentityConflictError,NameNotFoundError,NameRepositoryOperationError
from .postgresql_connection_provider import PostgreSQLConnectionProvider
from .postgresql_name_row_mapper import PostgreSQLNameRowMapper as Mapper
class PostgreSQLNameRepository(NameRepository):
    _SELECT="name_id,canonical_value,name_kind,status,runtime_mode,schema_version,created_at,source_reference,language_refs,country_refs,region_refs,culture_refs,script_code,attributes"
    def __init__(self,provider:PostgreSQLConnectionProvider)->None:
        if not isinstance(provider,PostgreSQLConnectionProvider): raise TypeError("provider must be PostgreSQLConnectionProvider.")
        self._provider=provider
    @staticmethod
    def _id(value:object)->str:
        if not isinstance(value,str): raise TypeError("name_id must be text.")
        value=value.strip()
        if not value: raise ValueError("name_id cannot be empty.")
        return value
    def _run(self,operation):
        conn=self._provider.connect()
        try:
            result=operation(conn); conn.commit(); return result
        except (NameAlreadyExistsError,NameIdentityConflictError,NameNotFoundError):
            try: conn.rollback()
            finally: raise
        except Exception as exc:
            try: conn.rollback()
            finally: raise NameRepositoryOperationError("PostgreSQL name repository operation failed.") from exc
        finally:
            close=getattr(conn,"close",None)
            if callable(close): close()
    def add(self,record:CanonicalName)->CanonicalName:
        if not isinstance(record,CanonicalName): raise TypeError("record must be CanonicalName.")
        def op(conn):
            cur=conn.cursor()
            cur.execute("SELECT name_id FROM reference.canonical_name WHERE name_id=%s",(record.name_id,))
            if cur.fetchone() is not None: raise NameAlreadyExistsError("name_id already exists.")
            cur.execute("SELECT name_id FROM reference.canonical_name WHERE runtime_mode=%s AND name_kind=%s AND search_value=%s",record.identity_key)
            found=cur.fetchone()
            if found is not None: raise NameIdentityConflictError(f"equivalent canonical name already exists as {found[0]}.")
            cur.execute("INSERT INTO reference.canonical_name (name_id,canonical_value,search_value,name_kind,status,runtime_mode,schema_version,created_at,source_reference,language_refs,country_refs,region_refs,culture_refs,script_code,attributes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s::jsonb)",Mapper.parameters(record)); return record
        return self._run(op)
    def get(self,name_id:str)->CanonicalName:
        ident=self._id(name_id)
        def op(conn):
            cur=conn.cursor(); cur.execute(f"SELECT {self._SELECT} FROM reference.canonical_name WHERE name_id=%s",(ident,)); row=cur.fetchone()
            if row is None: raise NameNotFoundError("canonical name was not found.")
            return Mapper.to_record(row)
        return self._run(op)
    def replace(self,record:CanonicalName)->CanonicalName:
        if not isinstance(record,CanonicalName): raise TypeError("record must be CanonicalName.")
        def op(conn):
            cur=conn.cursor(); cur.execute("SELECT name_id FROM reference.canonical_name WHERE name_id=%s FOR UPDATE",(record.name_id,))
            if cur.fetchone() is None: raise NameNotFoundError("canonical name was not found.")
            cur.execute("SELECT name_id FROM reference.canonical_name WHERE runtime_mode=%s AND name_kind=%s AND search_value=%s AND name_id<>%s",record.identity_key+(record.name_id,))
            found=cur.fetchone()
            if found is not None: raise NameIdentityConflictError(f"equivalent canonical name already exists as {found[0]}.")
            p=Mapper.parameters(record)
            cur.execute("UPDATE reference.canonical_name SET canonical_value=%s,search_value=%s,name_kind=%s,status=%s,runtime_mode=%s,schema_version=%s,created_at=%s,source_reference=%s,language_refs=%s::jsonb,country_refs=%s::jsonb,region_refs=%s::jsonb,culture_refs=%s::jsonb,script_code=%s,attributes=%s::jsonb WHERE name_id=%s",p[1:]+(p[0],)); return record
        return self._run(op)
    def exists(self,name_id:str)->bool:
        ident=self._id(name_id)
        return self._run(lambda c:(lambda cur:(cur.execute("SELECT 1 FROM reference.canonical_name WHERE name_id=%s",(ident,)),cur.fetchone() is not None)[1])(c.cursor()))
    def count(self)->int:
        return self._run(lambda c:(lambda cur:(cur.execute("SELECT COUNT(*) FROM reference.canonical_name"),int(cur.fetchone()[0]))[1])(c.cursor()))
    def list_all(self)->tuple[CanonicalName,...]:
        def op(conn):
            cur=conn.cursor(); cur.execute(f"SELECT {self._SELECT} FROM reference.canonical_name ORDER BY runtime_mode,name_kind,search_value,name_id"); return tuple(Mapper.to_record(r) for r in cur.fetchall())
        return self._run(op)
    def search(self,query:NameSearchQuery)->NameSearchResult:
        if not isinstance(query,NameSearchQuery): raise TypeError("query must be NameSearchQuery.")
        clauses=[]; params=[]
        if query.name_kind is not None: clauses.append("name_kind=%s"); params.append(query.name_kind.value)
        if query.status is not None: clauses.append("status=%s"); params.append(query.status.value)
        if query.runtime_mode is not None: clauses.append("runtime_mode=%s"); params.append(query.runtime_mode)
        needle=comparison_key(query.text)
        if needle: clauses.append("search_value=%s" if query.exact else "search_value LIKE %s"); params.append(needle if query.exact else needle+"%")
        where=" WHERE "+" AND ".join(clauses) if clauses else ""
        def op(conn):
            cur=conn.cursor(); cur.execute("SELECT COUNT(*) FROM reference.canonical_name"+where,tuple(params)); total=int(cur.fetchone()[0]); cur.execute(f"SELECT {self._SELECT} FROM reference.canonical_name"+where+" ORDER BY runtime_mode,name_kind,search_value,name_id LIMIT %s OFFSET %s",tuple(params+[query.limit,query.offset])); rows=tuple(Mapper.to_record(r) for r in cur.fetchall()); return NameSearchResult(rows,total,query.limit,query.offset)
        return self._run(op)
__all__=["PostgreSQLNameRepository"]
