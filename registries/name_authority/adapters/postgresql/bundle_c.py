"""PostgreSQL adapters for Bundle C generation and read access.

These adapters use bounded, parameterized writes. They intentionally do not interpret
raw seed files and do not alter Bundle B repositories.
"""
from __future__ import annotations
import json
from registries.name_authority.generation import *
from registries.name_authority.read_models import *
from registries.name_authority.authority import AuthorityNameComposition,AuthorityNameStatus

class PostgreSQLGenerationRepository:
    def __init__(self,provider): self.provider=provider
    def save_batch(self,batch):
        c=self.provider.connect()
        try:
            cur=c.cursor(); r=batch.request
            cur.execute("INSERT INTO reference.name_generation_batch (generation_batch_id,runtime_mode,source_snapshot_id,source_snapshot_checksum,requested_count,batch_size,random_seed,generator_algorithm,generator_version,rules_version,status,next_sequence,attempted_count,inserted_count,existing_count,skipped_count,failed_count,checkpoint_sequence,row_version,created_at,completed_at,result_checksum,configuration) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) ON CONFLICT (generation_batch_id) DO UPDATE SET status=EXCLUDED.status,next_sequence=EXCLUDED.next_sequence,attempted_count=EXCLUDED.attempted_count,inserted_count=EXCLUDED.inserted_count,existing_count=EXCLUDED.existing_count,skipped_count=EXCLUDED.skipped_count,failed_count=EXCLUDED.failed_count,checkpoint_sequence=EXCLUDED.checkpoint_sequence,row_version=EXCLUDED.row_version,completed_at=EXCLUDED.completed_at,result_checksum=EXCLUDED.result_checksum",(batch.generation_batch_id,r.runtime_mode,r.source_snapshot_id,r.source_snapshot_checksum,r.requested_count,r.batch_size,r.random_seed,r.generator_algorithm,r.generator_version,r.rules_version,batch.status.value,batch.next_sequence,batch.attempted_count,batch.inserted_count,batch.existing_count,batch.skipped_count,batch.failed_count,batch.checkpoint_sequence,batch.row_version,batch.created_at,batch.completed_at,batch.result_checksum,json.dumps({"targets":[{"family":x.family.value,"requested_count":x.requested_count} for x in r.targets]})))
            c.commit(); return batch
        except Exception: c.rollback(); raise
        finally:
            if callable(getattr(c,"close",None)): c.close()

class PostgreSQLNameAuthorityReadRepository:
    def __init__(self,provider): self.provider=provider
    def search(self,q):
        c=self.provider.connect()
        try:
            cur=c.cursor(); cursor=NameAuthoritySearchCursor.decode(q.cursor) if q.cursor else None
            clauses=["runtime_mode=%s"]; params=[q.runtime_mode]
            if q.text: clauses.append("search_name = %s" if q.exact else "search_name LIKE %s"); params.append(q.text.casefold() if q.exact else q.text.casefold()+"%")
            if cursor: clauses.append("(search_name,authority_name_id)>(%s,%s)"); params += [cursor.search_name,cursor.authority_name_id]
            sql="SELECT authority_name_id,runtime_mode,composition_type,display_name,search_name,ordered_component_ids,ordered_component_values,source_strategy,status,generation_family,generation_batch_id,schema_version,read_model_version,projected_at,metadata FROM reference.name_authority_read_model WHERE "+" AND ".join(clauses)+" ORDER BY search_name,authority_name_id LIMIT %s"; params.append(q.limit+1)
            cur.execute(sql,tuple(params)); rows=cur.fetchall(); more=len(rows)>q.limit; rows=rows[:q.limit]
            items=[]
            for x in rows:
                meta=x[14] if not isinstance(x[14],str) else json.loads(x[14]); items.append(NameAuthorityReadModel(x[0],x[1],AuthorityNameComposition.parse(x[2]),x[3],x[4],tuple(x[5]),tuple(x[6]),x[7],AuthorityNameStatus(x[8]),x[9],x[10],x[11],x[12],x[13],meta))
            nxt=NameAuthoritySearchCursor(q.runtime_mode,items[-1].search_name,items[-1].authority_name_id,items[-1].read_model_version).encode() if more and items else None
            return NameAuthoritySearchResult(tuple(items),nxt,more,q.runtime_mode,items[0].read_model_version if items else 1)
        finally:
            if callable(getattr(c,"close",None)): c.close()
