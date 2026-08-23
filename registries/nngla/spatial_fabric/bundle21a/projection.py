"""Create public projection records only after a durable publication gate succeeds."""
from __future__ import annotations
from ._shared import TARGET_RUNTIME,READ_MODEL_VERSION,stable_id
from .contracts import PublicationCandidate,PublicationDecision,PublicProjectionRecord,DurablePublicationRecord,content_sha256
from .eligibility import decide

def publish(candidate:PublicationCandidate, *, geometry_id:str, geometry_version:int=1, naming_status:str|None=None, geometry_publication_status:str|None=None, submitted_by:str, approved_by:str):
    # First evaluate prerequisites without the gate, then create the gate evidence, then evaluate with the gate.
    pre=decide(candidate,published_through_gate=False,live_geometry_id=geometry_id,live_name_status=naming_status,live_geometry_publication_status=geometry_publication_status)
    nongate=tuple(r for r in pre.reasons if r!='NO_NNGLA_PUBLICATION_RECORD')
    if nongate: return pre,None,None
    final=decide(candidate,published_through_gate=True,live_geometry_id=geometry_id,live_name_status=naming_status,live_geometry_publication_status=geometry_publication_status)
    if final.decision!='PUBLIC': return final,None,None
    payload={'subject_id':candidate.subject_id,'record_family':candidate.record_family,'runtime_mode':TARGET_RUNTIME,'geometry_id':geometry_id,'geometry_version':geometry_version,'display_name':candidate.display_name}
    pub=DurablePublicationRecord(final.publication_id,candidate.subject_id,candidate.record_family,TARGET_RUNTIME,geometry_id,geometry_version,approved_by,submitted_by,content_sha256(payload))
    projection=PublicProjectionRecord(stable_id('read:nngla:',candidate.subject_id,TARGET_RUNTIME,READ_MODEL_VERSION),candidate.subject_id,candidate.record_family,candidate.display_name,TARGET_RUNTIME,pub.publication_id,geometry_id,geometry_version,READ_MODEL_VERSION)
    return final,pub,projection
