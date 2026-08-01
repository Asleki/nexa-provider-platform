"""Governed orchestration around locked validation and import contracts."""
from __future__ import annotations
import hashlib
from datetime import datetime,timezone
from registries.name_imports.name_candidate_status import NameCandidateStatus
from registries.name_imports.name_candidate_validator import NameCandidateValidator
from registries.name_imports.name_import_batch import NameImportBatch
from registries.name_imports.controlled_name_batch_importer import ControlledNameBatchImporter
from registries.names.name_repository import NameRepository
from .adapters import ProductionSeedAdapter,load_tribe_ids
from .models import GovernedImportReport,SeedManifest
from .seed_loader import ProductionSeedLoader

def _id(prefix:str,value:str)->str: return prefix+hashlib.sha256(value.encode()).hexdigest()[:24]
class GovernedAtomicNameImporter:
    def __init__(self,loader:ProductionSeedLoader,repository:NameRepository,*,clock=lambda:datetime.now(timezone.utc),name_id_factory=None):
        self.loader=loader; self.repository=repository; self.clock=clock; self.name_id_factory=name_id_factory or (lambda:_id("name:",str(self.clock().timestamp())))
    def run(self,manifest:SeedManifest,*,runtime_mode:str)->GovernedImportReport:
        runtime=self.loader.validate_runtime(manifest,runtime_mode); self.loader.validate(manifest)
        operation_id=_id("nameimportop:",f"{manifest.dataset_id}|{manifest.dataset_version}|{runtime}")
        tribe_ids=frozenset()
        refs=[f for f in manifest.files if f.record_role=="supporting_reference"]
        if refs: tribe_ids=load_tribe_ids(self.loader.rows(manifest,refs[0]))
        adapter=ProductionSeedAdapter(manifest,runtime,tribe_ids=tribe_ids,clock=self.clock)
        validator=NameCandidateValidator(); candidates=[]; quarantined=0; rejected=0
        for file in manifest.files:
            if not file.import_enabled: continue
            for row in self.loader.rows(manifest,file):
                try: produced=adapter.adapt(row,_id("namebatch:",f"{manifest.dataset_id}|{file.file_id}|{runtime}"))
                except Exception: rejected+=1; continue
                for candidate in produced:
                    result=validator.validate(candidate,batch_runtime_mode=runtime).result
                    if not result.is_valid: rejected+=1; continue
                    if result.warnings: quarantined+=1; continue
                    candidates.append(candidate.with_status(NameCandidateStatus.VALIDATED))
        imported=existing=failed=validated=0; batch_ids=[]
        by_source={}
        for c in candidates: by_source.setdefault((c.batch_id,c.source_id),[]).append(c)
        for (batch_id,source_id),values in by_source.items():
            batch=NameImportBatch(batch_id,runtime,source_id,source_id,tuple(values),created_at=self.clock()).approve(); batch_ids.append(batch_id); validated+=len(values)
            result=ControlledNameBatchImporter(self.repository,name_id_factory=self.name_id_factory,clock=self.clock).import_batch(batch)
            imported+=result.imported_count; existing+=result.existing_count; failed+=result.failed_count
        return GovernedImportReport(operation_id,manifest.dataset_id,runtime,len(candidates)+quarantined+rejected,validated,quarantined,rejected,imported,existing,failed,tuple(batch_ids))
__all__=["GovernedAtomicNameImporter"]
