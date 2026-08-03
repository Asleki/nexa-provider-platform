"""Execute exactly one governed catalogue-plan source file."""
from __future__ import annotations
import hashlib, unicodedata
from datetime import datetime, timezone
from registries.name_authority import ProductionSeedLoader, ProductionSeedAdapter, load_tribe_ids
from registries.name_authority.production_context import NameOrthographyProfile, NameStructureType
from .preview import _sample
from registries.name_imports.name_candidate_validator import NameCandidateValidator
from registries.name_imports.name_candidate_status import NameCandidateStatus
from registries.name_imports.name_import_batch import NameImportBatch
from registries.name_imports.controlled_name_batch_importer import ControlledNameBatchImporter
from .contracts import CataloguePlanStepReceipt

def _stable(prefix,material): return prefix+hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
def classify(value):
    if "-" in value: return NameStructureType.HYPHENATED
    if "'" in value or "’" in value: return NameStructureType.APOSTROPHIZED
    if len(value.split())>1:
        prefixes={"de","del","du","van","von","der","la","le"}
        return NameStructureType.PREFIXED_COMPOUND if value.split()[0].casefold() in prefixes or any(x.casefold() in prefixes for x in value.split()[:-1]) else NameStructureType.COMPOUND_SPACE_SEPARATED
    return NameStructureType.SIMPLE

class GovernedCataloguePlanStepExecutor:
    def __init__(self,loader,name_repository,context_repository,*,clock=lambda:datetime.now(timezone.utc)):
        self.loader=loader; self.names=name_repository; self.contexts=context_repository; self.clock=clock
    def execute(self,step,request,preview_step):
        manifest=self.loader.load_manifest(step.manifest_path); runtime=self.loader.validate_runtime(manifest,request.runtime_mode); self.loader.validate(manifest)
        contract=next((x for x in manifest.files if x.file_id==step.file_id),None)
        if contract is None: raise ValueError("plan step file was not found in its manifest.")
        rows=self.loader.rows(manifest,contract); selected,source_ids,fingerprint,distribution=_sample(rows,request.sample_size,request.random_seed+list(get_plan_steps(request.plan_id)).index(step))
        if fingerprint!=preview_step.selection_fingerprint: raise ValueError("catalogue plan preview no longer matches selected source rows.")
        refs=[x for x in manifest.files if x.record_role=="supporting_reference"]
        tribe_ids=load_tribe_ids(self.loader.rows(manifest,refs[0])) if refs else frozenset()
        adapter=ProductionSeedAdapter(manifest,runtime,tribe_ids=tribe_ids,clock=self.clock); validator=NameCandidateValidator(); candidates=[]; quarantined=rejected=0
        batch_id=_stable("namebatch:",f"{request.plan_id}|{step.step_id}|{runtime}|{fingerprint}")
        for row in selected:
            try: produced=adapter.adapt(row,batch_id)
            except Exception: rejected+=1; continue
            for candidate in produced:
                result=validator.validate(candidate,batch_runtime_mode=runtime).result
                if not result.is_valid: rejected+=1
                elif result.warnings: quarantined+=1
                else: candidates.append(candidate.with_status(NameCandidateStatus.VALIDATED))
        batch=NameImportBatch(batch_id,runtime,contract.file_id,contract.path,tuple(candidates),source_checksum=contract.sha256,created_at=self.clock()).approve()
        counter=iter(_stable("name:",f"{batch_id}|{c.candidate_id}") for c in batch.candidates)
        result=ControlledNameBatchImporter(self.names,name_id_factory=lambda:next(counter),clock=self.clock).import_batch(batch)
        profiles_created=profiles_existing=0
        candidate_by_id={x.candidate_id:x for x in batch.candidates}
        for item in result.items:
            if not item.canonical_name_id: continue
            candidate=candidate_by_id[item.candidate_id]; existing=self.contexts.get_profile_by_name(item.canonical_name_id)
            profile=NameOrthographyProfile(_stable("orth:",f"{item.canonical_name_id}|{contract.file_id}"),item.canonical_name_id,runtime,classify(unicodedata.normalize("NFC",candidate.raw_name_value)),candidate.raw_name_value,request.submitter_actor_id,request.approver_actor_id,source_reference=contract.file_id,attributes={"plan_id":request.plan_id,"step_id":step.step_id,"selection_fingerprint":fingerprint})
            stored=self.contexts.add_profile(profile)
            if existing is None: profiles_created+=1
            else: profiles_existing+=1
        failed=result.failed_count
        outcome="passed" if failed==0 else "failed"
        return CataloguePlanStepReceipt(step.step_id,step.file_id,step.target_kind,len(selected),len(candidates),result.imported_count,result.existing_count,quarantined,rejected,failed,profiles_created,profiles_existing,outcome,fingerprint)

def get_plan_steps(plan_id):
    from registries.name_authority.production_context import get_plan
    return get_plan(plan_id).steps
__all__=["GovernedCataloguePlanStepExecutor","classify"]
