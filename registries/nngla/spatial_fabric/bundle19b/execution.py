"""Governed all-or-nothing initial administrative boundary legalization."""
from __future__ import annotations
from dataclasses import asdict
from ._shared import BUNDLE_CODE,BUNDLE_EFFECTIVE_DATE,INPUT_PATHS,ROOT,payload_sha256,sha256_path
from .authoring import load_boundary_candidates
from .contracts import AdministrativeBoundaryExecutionReceipt
from .legalization import load_legalization_decisions
from .qualification import qualification_findings

def bundle_source_hashes(): return tuple((p.relative_to(ROOT).as_posix(),sha256_path(p)) for p in INPUT_PATHS)
def bundle_fingerprint():
    return payload_sha256({'bundle_code':BUNDLE_CODE,'effective_date':BUNDLE_EFFECTIVE_DATE,'source_hashes':bundle_source_hashes(),'boundaries':[asdict(x) for x in load_boundary_candidates()],'legalization':list(load_legalization_decisions())})
def execute_administrative_boundary_legalization(repository,submitter_actor_id,approver_actor_id,repository_revision='bundle19-working-tree'):
    submitter=str(submitter_actor_id).strip();approver=str(approver_actor_id).strip()
    if not submitter or not approver or submitter==approver: raise ValueError('distinct submitter and approver are required')
    findings=qualification_findings()
    if findings: raise RuntimeError('Bundle 19B qualification failed: '+','.join(findings))
    f=bundle_fingerprint(); replay=repository.replay(f)
    if replay:return replay
    repository.preflight(); boundaries=load_boundary_candidates()
    for b in boundaries: repository.qualify_geometry(b)
    execution_id='nnglarun:admin-boundary:'+f[:32]; details=[]
    with repository.transaction():
        for b in boundaries:
            gid=repository.reserve_geometry(b); repository.persist_geometry(b,gid); repository.legalize(b,gid)
            details.append({'administrative_area_id':b.administrative_area_id,'administrative_candidate_id':b.administrative_candidate_id,'source_record_id':b.source_record_id,'geometry_id':gid,'geometry_role_code':'ADMINISTRATIVE_BOUNDARY','boundary_status':'LEGALIZED','lifecycle_status':'ACTIVE','publication_ready':False})
        r=AdministrativeBoundaryExecutionReceipt(execution_id,f,repository.database_name,repository.environment_name,repository_revision,submitter,approver,192,192,192,'APPLIED',False)
        repository.persist_execution_receipt(r,tuple(details)); return r
