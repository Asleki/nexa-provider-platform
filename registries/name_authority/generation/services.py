"""Deterministic simulation generation and checkpoint processing."""
from __future__ import annotations
from dataclasses import replace
import hashlib, math
from .contracts import *
from registries.name_authority.authority import AuthorityNameBuilder,AuthorityNameComposition,AuthorityComponentRole
from registries.names import NameKind

class GenerationCapacityService:
    def calculate(self,snapshot,request):
        f=len(snapshot.by_kind(NameKind.FIRST_NAME)); m=len(snapshot.by_kind(NameKind.MIDDLE_NAME)); s=len(snapshot.by_kind(NameKind.SURNAME))
        out=[]
        for t in request.targets:
            if t.family in {SimulationNameGenerationFamily.NOVEGEO_NATIVE_THREE_PART,SimulationNameGenerationFamily.MULTICULTURAL_THREE_PART}: cap=f*m*s
            elif t.family is SimulationNameGenerationFamily.IMMIGRATION_APPROVED_PAIR:
                cap=len({x.source_pair_key for x in snapshot.members if x.source_pair_key})
            else: cap=f*s
            out.append(GenerationCapacity(t.family,cap,cap,t.requested_count))
        return tuple(out)

class DeterministicCombinationSequence:
    def __init__(self,seed): self.seed=seed
    def permuted_index(self,sequence,capacity):
        if capacity<1: raise ValueError("capacity must be positive.")
        digest=hashlib.sha256(f"{self.seed}|{capacity}".encode()).digest()
        start=int.from_bytes(digest[:8],"big")%capacity
        step=(int.from_bytes(digest[8:16],"big")%(capacity-1)+1) if capacity>1 else 1
        while math.gcd(step,capacity)!=1: step=(step+1)%capacity or 1
        return (start+sequence*step)%capacity

class SimulationNameGenerator:
    def __init__(self,builder=None): self.builder=builder or AuthorityNameBuilder()
    @staticmethod
    def _profiles(snapshot): return snapshot.by_kind(NameKind.FIRST_NAME),snapshot.by_kind(NameKind.MIDDLE_NAME),snapshot.by_kind(NameKind.SURNAME)
    def generate(self,snapshot,request,start_sequence,count):
        if snapshot.snapshot_id!=request.source_snapshot_id or snapshot.checksum!=request.source_snapshot_checksum: raise ValueError("generation request does not match source snapshot.")
        first,middle,surname=self._profiles(snapshot); seq=DeterministicCombinationSequence(request.random_seed)
        family_ranges=[]; cursor=0
        for target in request.targets: family_ranges.append((cursor,cursor+target.requested_count,target)); cursor+=target.requested_count
        end=min(start_sequence+count,request.requested_count); out=[]
        for global_seq in range(start_sequence,end):
            lo,hi,target=next(x for x in family_ranges if x[0]<=global_seq<x[1]); local=global_seq-lo; fam=target.family
            if fam in {SimulationNameGenerationFamily.NOVEGEO_NATIVE_THREE_PART,SimulationNameGenerationFamily.MULTICULTURAL_THREE_PART}:
                capacity=len(first)*len(middle)*len(surname); idx=seq.permuted_index(local,capacity); si=idx%len(surname); idx//=len(surname); mi=idx%len(middle); fi=(idx//len(middle))%len(first)
                atoms=(first[fi],middle[mi],surname[si]); comp=AuthorityNameComposition.FIRST_MIDDLE_SURNAME; roles=(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.MIDDLE_NAME,AuthorityComponentRole.SURNAME)
            elif fam is SimulationNameGenerationFamily.IMMIGRATION_APPROVED_PAIR:
                pairs={}
                for p in snapshot.members:
                    if p.source_pair_key: pairs.setdefault(p.source_pair_key,{})[p.name_kind]=p
                valid=[v for _,v in sorted(pairs.items()) if NameKind.FIRST_NAME in v and NameKind.SURNAME in v]
                if not valid: raise ValueError("immigration pair capacity is empty.")
                pair=valid[seq.permuted_index(local,len(valid))]; atoms=(pair[NameKind.FIRST_NAME],pair[NameKind.SURNAME]); comp=AuthorityNameComposition.INTERNATIONAL_PAIR; roles=(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME)
            else:
                capacity=len(first)*len(surname); idx=seq.permuted_index(local,capacity); fi=(idx//len(surname))%len(first); si=idx%len(surname)
                atoms=(first[fi],surname[si]); comp=AuthorityNameComposition.FIRST_SURNAME; roles=(AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME)
            canonical=tuple(_profile_as_name(x) for x in atoms)
            record=self.builder.build(comp,canonical,roles,actor_id="simulation-generator",runtime_mode="simulation",metadata={"generation":{"batch_id":request.generation_batch_id,"sequence":global_seq,"family":fam.value,"generator_algorithm":request.generator_algorithm,"generator_version":request.generator_version,"rules_version":request.rules_version,"source_snapshot_id":snapshot.snapshot_id}})
            out.append((global_seq,fam,record))
        return tuple(out)

def _profile_as_name(p):
    from registries.names import CanonicalName,NameMetadata
    return CanonicalName(p.name_id,p.canonical_value,p.name_kind,NameMetadata(runtime_mode="simulation",attributes=dict(p.metadata)))

class GenerationResumeValidator:
    def validate(self,batch,request,snapshot):
        if batch.generation_batch_id!=request.generation_batch_id or batch.request!=request: raise ValueError("resume request differs from persisted batch contract.")
        if snapshot.snapshot_id!=request.source_snapshot_id or snapshot.checksum!=request.source_snapshot_checksum: raise ValueError("resume source snapshot changed.")
        if batch.status not in {GenerationBatchStatus.READY,GenerationBatchStatus.RUNNING,GenerationBatchStatus.PAUSED}: raise ValueError("batch is not resumable.")
        return True

class GenerationBatchProcessor:
    def __init__(self,generator,repository,bulk_writer): self.generator=generator; self.repository=repository; self.bulk_writer=bulk_writer
    def run_next(self,batch,snapshot):
        if batch.status is GenerationBatchStatus.READY: batch=batch.transition(GenerationBatchStatus.RUNNING)
        if batch.status is not GenerationBatchStatus.RUNNING: raise ValueError("batch must be running.")
        remaining=batch.request.requested_count-batch.next_sequence
        if remaining<=0: return batch.transition(GenerationBatchStatus.COMPLETED)
        generated=self.generator.generate(snapshot,batch.request,batch.next_sequence,min(batch.request.batch_size,remaining))
        outcomes=self.bulk_writer.write(batch,generator_records=generated)
        checksum=_results_checksum(outcomes)
        first=batch.next_sequence; next_seq=first+len(generated)
        checkpoint=GenerationCheckpoint(f"checkpoint:{batch.generation_batch_id}:{batch.checkpoint_sequence+1}",batch.generation_batch_id,batch.checkpoint_sequence+1,first,next_seq-1,next_seq,len(outcomes),sum(x.outcome is GenerationResultOutcome.INSERTED for x in outcomes),sum(x.outcome is GenerationResultOutcome.EXISTING for x in outcomes),sum(x.outcome is GenerationResultOutcome.SKIPPED for x in outcomes),sum(x.outcome is GenerationResultOutcome.FAILED for x in outcomes),checksum,snapshot.checksum)
        updated=replace(batch,next_sequence=next_seq,attempted_count=batch.attempted_count+len(outcomes),inserted_count=batch.inserted_count+checkpoint.inserted_count,existing_count=batch.existing_count+checkpoint.existing_count,skipped_count=batch.skipped_count+checkpoint.skipped_count,failed_count=batch.failed_count+checkpoint.failed_count,checkpoint_sequence=checkpoint.checkpoint_sequence,row_version=batch.row_version+1)
        if updated.next_sequence>=updated.request.requested_count: updated=updated.transition(GenerationBatchStatus.COMPLETED); updated=replace(updated,result_checksum=hashlib.sha256((checksum+updated.generation_batch_id).encode()).hexdigest())
        self.repository.commit(GenerationBatchCommit(updated,tuple(outcomes),checkpoint)); return updated

def _results_checksum(results):
    raw="\n".join(f"{x.generation_sequence}|{x.composition_key}|{x.authority_name_id}|{x.outcome.value}" for x in sorted(results,key=lambda r:r.generation_sequence))
    return hashlib.sha256(raw.encode()).hexdigest()
