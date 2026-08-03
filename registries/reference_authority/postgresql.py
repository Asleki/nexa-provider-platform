"""PostgreSQL reference repository and atomic sequence allocator."""
from __future__ import annotations
import json
from .contracts import ReferenceRecord,ReferenceType
class PostgreSQLReferenceRepository:
    def __init__(self,provider): self.provider=provider
    def _run(self,fn):
        c=self.provider.connect()
        try:r=fn(c); c.commit(); return r
        except Exception: c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    def add(self,r):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT reference_id,reference_code,reference_type,canonical_label,runtime_mode,status,source_reference,origin_type,native_label,attributes,created_at,created_by_actor_id,approved_by_actor_id FROM reference.reference_authority_record WHERE runtime_mode=%s AND reference_type=%s AND search_label=%s",(r.runtime_mode,r.reference_type.value,r.search_label)); row=cur.fetchone()
            if row: return self._map(row)
            cur.execute("INSERT INTO reference.reference_authority_record(reference_id,reference_code,reference_type,canonical_label,search_label,runtime_mode,status,source_reference,origin_type,native_label,attributes,created_at,created_by_actor_id,approved_by_actor_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)",(r.reference_id,r.reference_code,r.reference_type.value,r.canonical_label,r.search_label,r.runtime_mode,r.status.value,r.source_reference,None if r.origin_type is None else r.origin_type.value,r.native_label,json.dumps(dict(r.attributes),ensure_ascii=False),r.created_at,r.created_by_actor_id,r.approved_by_actor_id)); return r
        return self._run(op)
    def get(self,i):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT reference_id,reference_code,reference_type,canonical_label,runtime_mode,status,source_reference,origin_type,native_label,attributes,created_at,created_by_actor_id,approved_by_actor_id FROM reference.reference_authority_record WHERE reference_id=%s",(i,)); row=cur.fetchone()
            if not row: raise KeyError("reference was not found.")
            return self._map(row)
        return self._run(op)
    def find(self,t,rt,s):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT reference_id,reference_code,reference_type,canonical_label,runtime_mode,status,source_reference,origin_type,native_label,attributes,created_at,created_by_actor_id,approved_by_actor_id FROM reference.reference_authority_record WHERE reference_type=%s AND runtime_mode=%s AND search_label=%s",(t,rt,s)); row=cur.fetchone(); return None if row is None else self._map(row)
        return self._run(op)
    def list_all(self):
        return self._run(lambda c:(lambda cur:(cur.execute("SELECT reference_id,reference_code,reference_type,canonical_label,runtime_mode,status,source_reference,origin_type,native_label,attributes,created_at,created_by_actor_id,approved_by_actor_id FROM reference.reference_authority_record ORDER BY reference_type,reference_code"),tuple(self._map(r) for r in cur.fetchall()))[1])(c.cursor()))
    @staticmethod
    def _map(r):
        a=json.loads(r[9]) if isinstance(r[9],str) else (r[9] or {})
        return ReferenceRecord(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],a,r[10],r[11],r[12])
class PostgreSQLReferenceCodeAllocator:
    SEQ={ReferenceType.TRIBE:"reference.tribe_code_seq",ReferenceType.LANGUAGE:"reference.language_code_seq",ReferenceType.ORIGIN:"reference.origin_code_seq"}
    def __init__(self,provider): self.provider=provider
    def __call__(self,t):
        c=self.provider.connect()
        try:
            cur=c.cursor(); cur.execute(f"SELECT nextval('{self.SEQ[ReferenceType.parse(t)]}')"); n=int(cur.fetchone()[0]); c.commit(); return n
        except Exception: c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
__all__=["PostgreSQLReferenceRepository","PostgreSQLReferenceCodeAllocator"]
