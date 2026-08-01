"""PostgreSQL persistence adapters for M009.12 Bundle B."""
from __future__ import annotations
import json
from datetime import datetime
from registries.adapters.postgresql import PostgreSQLConnectionProvider
from registries.name_authority.manual import ManualNameCandidate,ManualNameCandidateStatus,ProductionManualNameRequest,ActorContext,ReferenceDeclaration,ReferenceKnowledgeState,ReferenceBindingState
from registries.name_authority.authority import NameAuthorityRecord,AuthorityNameComponent,AuthorityNameComposition,AuthorityComponentRole,AuthorityNameStatus
from registries.names import NameKind
from registries.names.name_sex_usage import NameSexUsage

class PostgreSQLManualNameCandidateRepository:
    def __init__(self,provider): self.provider=provider
    def _run(self,fn):
        c=self.provider.connect()
        try:r=fn(c); c.commit(); return r
        except Exception:
            c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    @staticmethod
    def _decl(d): return json.dumps({"knowledge_state":d.knowledge_state.value,"binding_state":d.binding_state.value,"label":d.label,"reference_id":d.reference_id},ensure_ascii=False)
    def add(self,candidate):
        def op(c):
            cur=c.cursor(); r=candidate.request
            cur.execute("INSERT INTO reference.manual_name_candidate (candidate_id,request_id,operation_id,runtime_mode,raw_name_value,requested_name_kind,sex_usage,origin_declaration,language_declaration,community_declaration,script_code,status,schema_version,submitted_by_actor_id,submitted_by_actor_type,submitted_at,notes,canonical_name_id,reviewed_by_actor_id,reviewed_at,decision_reason) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(
                candidate.candidate_id,r.request_id,r.operation_id,r.runtime_mode,r.raw_name_value,r.requested_name_kind.value,r.sex_usage.value,self._decl(r.origin),self._decl(r.language),self._decl(r.community),r.script_code,candidate.status.value,r.schema_version,r.actor.actor_id,r.actor.actor_type,r.submitted_at,r.notes,candidate.canonical_name_id,candidate.reviewed_by_actor_id,candidate.reviewed_at,candidate.decision_reason)); return candidate
        return self._run(op)
    def get(self,candidate_id):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT candidate_id,request_id,operation_id,runtime_mode,raw_name_value,requested_name_kind,sex_usage,origin_declaration,language_declaration,community_declaration,script_code,status,schema_version,submitted_by_actor_id,submitted_by_actor_type,submitted_at,notes,canonical_name_id,reviewed_by_actor_id,reviewed_at,decision_reason FROM reference.manual_name_candidate WHERE candidate_id=%s",(candidate_id,)); row=cur.fetchone()
            if row is None: raise KeyError("candidate was not found.")
            def dec(v):
                if isinstance(v,str): v=json.loads(v)
                return ReferenceDeclaration(v.get("knowledge_state","unspecified"),v.get("binding_state","not_applicable"),v.get("label"),v.get("reference_id"))
            req=ProductionManualNameRequest(row[1],row[2],row[4],NameKind.parse(row[5]),NameSexUsage.parse(row[6]),ActorContext(row[13],row[14]),dec(row[7]),dec(row[8]),dec(row[9]),row[10],row[16],row[3],row[12],row[15])
            return ManualNameCandidate(row[0],req,ManualNameCandidateStatus.parse(row[11]),row[17],row[18],row[19],row[20])
        return self._run(op)
    def replace(self,candidate):
        def op(c):
            cur=c.cursor(); cur.execute("UPDATE reference.manual_name_candidate SET status=%s,canonical_name_id=%s,reviewed_by_actor_id=%s,reviewed_at=%s,decision_reason=%s WHERE candidate_id=%s",(candidate.status.value,candidate.canonical_name_id,candidate.reviewed_by_actor_id,candidate.reviewed_at,candidate.decision_reason,candidate.candidate_id))
            if getattr(cur,"rowcount",1)==0: raise KeyError("candidate was not found.")
            return candidate
        return self._run(op)

class PostgreSQLNameAuthorityRepository:
    def __init__(self,provider): self.provider=provider
    def _run(self,fn):
        c=self.provider.connect()
        try:r=fn(c); c.commit(); return r
        except Exception:
            c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    def create_or_get(self,record):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT authority_name_id FROM reference.name_authority_record WHERE runtime_mode=%s AND composition_key=%s",(record.runtime_mode,record.composition_key)); row=cur.fetchone()
            if row is not None:
                authority_id=row[0]
                cur.execute("SELECT authority_name_id,runtime_mode,composition_type,composition_key,display_name,search_name,source_strategy,status,schema_version,created_at,created_by_actor_id,approved_at,approved_by_actor_id,supersedes_authority_name_id,metadata FROM reference.name_authority_record WHERE authority_name_id=%s",(authority_id,)); head=cur.fetchone()
                cur.execute("SELECT position,name_id,component_role,name_kind_snapshot,separator_after FROM reference.name_authority_component WHERE authority_name_id=%s ORDER BY position",(authority_id,)); parts=cur.fetchall()
                metadata=head[14]
                if isinstance(metadata,str): metadata=json.loads(metadata)
                components=tuple(AuthorityNameComponent(x[0],x[1],NameKind.parse(x[3]),AuthorityComponentRole.parse(x[2]),"",x[4]) for x in parts)
                return NameAuthorityRecord(head[0],head[1],AuthorityNameComposition.parse(head[2]),components,head[4],head[5],head[3],head[6],AuthorityNameStatus(head[7]),head[8],head[9],head[10],head[11],head[12],head[13],metadata)
            ids=tuple(x.name_id for x in record.components)
            cur.execute("SELECT name_id,status,runtime_mode FROM reference.canonical_name WHERE name_id = ANY(%s)",(list(ids),)); rows=cur.fetchall()
            if len(rows)!=len(ids): raise ValueError("one or more atomic names do not exist.")
            if any(r[1]!="active" or r[2]!=record.runtime_mode for r in rows): raise ValueError("atomic components must be active and runtime-consistent.")
            cur.execute("INSERT INTO reference.name_authority_record (authority_name_id,runtime_mode,composition_type,composition_key,display_name,search_name,source_strategy,status,schema_version,created_at,created_by_actor_id,approved_at,approved_by_actor_id,supersedes_authority_name_id,metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",(record.authority_name_id,record.runtime_mode,record.composition.value,record.composition_key,record.display_name,record.search_name,record.source_strategy,record.status.value,record.schema_version,record.created_at,record.created_by_actor_id,record.approved_at,record.approved_by_actor_id,record.supersedes_authority_name_id,json.dumps(dict(record.metadata))))
            for x in record.components: cur.execute("INSERT INTO reference.name_authority_component (authority_name_id,position,name_id,component_role,name_kind_snapshot,separator_after,metadata) VALUES (%s,%s,%s,%s,%s,%s,'{}'::jsonb)",(record.authority_name_id,x.position,x.name_id,x.role.value,x.name_kind.value,x.separator_after))
            return record
        return self._run(op)
    def get(self,authority_name_id):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT authority_name_id,runtime_mode,composition_type,composition_key,display_name,search_name,source_strategy,status,schema_version,created_at,created_by_actor_id,approved_at,approved_by_actor_id,supersedes_authority_name_id,metadata FROM reference.name_authority_record WHERE authority_name_id=%s",(authority_name_id,)); head=cur.fetchone()
            if head is None: raise KeyError("authority name was not found.")
            cur.execute("SELECT position,name_id,component_role,name_kind_snapshot,separator_after FROM reference.name_authority_component WHERE authority_name_id=%s ORDER BY position",(authority_name_id,)); parts=cur.fetchall(); metadata=head[14]
            if isinstance(metadata,str): metadata=json.loads(metadata)
            components=tuple(AuthorityNameComponent(x[0],x[1],NameKind.parse(x[3]),AuthorityComponentRole.parse(x[2]),"",x[4]) for x in parts)
            return NameAuthorityRecord(head[0],head[1],AuthorityNameComposition.parse(head[2]),components,head[4],head[5],head[3],head[6],AuthorityNameStatus(head[7]),head[8],head[9],head[10],head[11],head[12],head[13],metadata)
        return self._run(op)
    def find_equivalent(self,runtime_mode,composition_key):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT authority_name_id FROM reference.name_authority_record WHERE runtime_mode=%s AND composition_key=%s",(runtime_mode,composition_key)); row=cur.fetchone(); return None if row is None else row[0]
        ident=self._run(op); return None if ident is None else self.get(ident)
