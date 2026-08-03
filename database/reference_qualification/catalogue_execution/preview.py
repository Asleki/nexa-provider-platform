"""Read-only catalogue-plan preview generation."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from registries.name_authority import ProductionSeedLoader
from registries.name_authority.production_context import get_plan
import random
from .contracts import CataloguePlanPreview, CataloguePlanStepPreview

def _sample(rows,size,seed):
    rows=list(rows)
    if size<1 or size>len(rows): raise ValueError("sample size is outside source bounds.")
    rng=random.Random(int(seed)); rng.shuffle(rows)
    selected=tuple(rows[:size])
    ids=tuple(str(r.values.get("id") or r.values.get("ID") or r.row_number) for r in selected)
    material="|".join(ids)+f"|{seed}|diverse-v2"
    fp=hashlib.sha256(material.encode("utf-8")).hexdigest()
    distribution={}
    for field in ("gender","origin","language"):
        values=sorted({str(r.values.get(field) or r.values.get(field.title()) or "").casefold() for r in selected if str(r.values.get(field) or r.values.get(field.title()) or "").strip()})
        distribution[field]=values
    return selected,ids,fp,distribution

class CataloguePlanPreviewService:
    def __init__(self, seed_root="database/seeds", *, clock=lambda:datetime.now(timezone.utc)):
        self.seed_root=Path(seed_root); self.clock=clock
    def preview(self, request, *, database_name, environment):
        plan=get_plan(request.plan_id); loader=ProductionSeedLoader(self.seed_root); step_previews=[]
        for index,step in enumerate(plan.steps):
            manifest=loader.load_manifest(Path(step.manifest_path))
            loader.validate_runtime(manifest,request.runtime_mode); loader.validate(manifest)
            contracts=[x for x in manifest.files if x.file_id==step.file_id]
            if len(contracts)!=1: raise ValueError(f"plan step {step.step_id} does not resolve exactly one governed file.")
            contract=contracts[0]
            if not contract.import_enabled: raise ValueError(f"plan step {step.step_id} targets a non-importable file.")
            if contract.target_name_kind!=step.target_kind: raise ValueError(f"plan step {step.step_id} target kind disagrees with the manifest.")
            rows=loader.rows(manifest,contract)
            if request.sample_size>len(rows): raise ValueError(f"sample_size exceeds source rows for {step.step_id}.")
            selected,source_ids,fingerprint,distribution=_sample(rows,request.sample_size,request.random_seed+index)
            step_previews.append(CataloguePlanStepPreview(step.step_id,step.manifest_path,step.file_id,step.target_kind,step.classification,len(rows),source_ids,fingerprint,distribution))
        material={"plan_id":request.plan_id,"runtime":request.runtime_mode,"sample_size":request.sample_size,"random_seed":request.random_seed,"database":database_name,"environment":environment,"revision":request.repository_revision,"steps":[{"id":s.step_id,"file":s.file_id,"fingerprint":s.selection_fingerprint,"records":s.selected_source_record_ids} for s in step_previews]}
        fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()
        token=f"RUN CATALOGUE PLAN {request.plan_id} {database_name} {fingerprint[:12]}"
        return CataloguePlanPreview(request.plan_id,request.runtime_mode,request.sample_size,request.random_seed,database_name,environment,request.repository_revision,fingerprint,token,tuple(step_previews),request.sample_size*len(step_previews),self.clock())
__all__=["CataloguePlanPreviewService"]
