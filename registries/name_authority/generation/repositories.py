"""Memory generation repositories and bulk-writer port."""
from threading import RLock
from .contracts import *
class MemoryGenerationRepository:
    def __init__(self): self.batches={}; self.commits=[]; self.snapshots={}; self._lock=RLock()
    def add_snapshot(self,s): self.snapshots[s.snapshot_id]=s; return s
    def get_snapshot(self,i): return self.snapshots[i]
    def add_batch(self,b):
        if b.generation_batch_id in self.batches: raise ValueError("generation batch already exists.")
        self.batches[b.generation_batch_id]=b; return b
    def get_batch(self,i): return self.batches[i]
    def commit(self,c):
        with self._lock: self.batches[c.batch.generation_batch_id]=c.batch; self.commits.append(c); return c

class MemoryBulkNameAuthorityWriter:
    def __init__(self,authority_repository): self.authority_repository=authority_repository; self.sequence_keys=set()
    def write(self,batch,generator_records):
        out=[]
        for sequence,family,record in generator_records:
            key=(batch.generation_batch_id,sequence)
            if key in self.sequence_keys:
                existing=self.authority_repository.find_equivalent(record.runtime_mode,record.composition_key)
                out.append(GenerationResult(batch.generation_batch_id,sequence,family,existing.authority_name_id,record.composition_key,GenerationResultOutcome.EXISTING)); continue
            pre=self.authority_repository.find_equivalent(record.runtime_mode,record.composition_key)
            saved=self.authority_repository.create_or_get(record); self.sequence_keys.add(key)
            outcome=GenerationResultOutcome.EXISTING if pre else GenerationResultOutcome.INSERTED
            out.append(GenerationResult(batch.generation_batch_id,sequence,family,saved.authority_name_id,saved.composition_key,outcome))
        return tuple(out)
