"""Production semantic context orchestration."""
from uuid import uuid4
from .contracts import NameOrthographyProfile,NameContextRelationship,NameContextRole,ContextState
from .policies import ProductionNameContextPolicy
class NameProductionContextService:
    def __init__(self,context_repository,reference_repository,policy=None): self.contexts=context_repository; self.references=reference_repository; self.policy=policy or ProductionNameContextPolicy()
    def apply(self,request):
        self.policy.validate(request)
        refs={}
        for key,ident in (("language",request.language_reference_id),("origin",request.origin_reference_id),("tribe",request.tribe_reference_id)):
            if ident:
                ref=self.references.get(ident)
                if ref.runtime_mode!=request.runtime_mode: raise ValueError("cross-runtime name context is forbidden.")
                if ref.reference_type.value!=key: raise ValueError(f"{key} reference has the wrong type.")
                refs[key]=ref
        p=NameOrthographyProfile(profile_id=f"orth:{uuid4().hex}",name_id=request.name_id,runtime_mode=request.runtime_mode,structure_type=request.structure_type,canonical_value_snapshot=request.canonical_value,created_by_actor_id=request.submitter_actor_id,approved_by_actor_id=request.approver_actor_id,source_reference=request.source_reference)
        p=self.contexts.add_profile(p); rel=[]
        def add(role,state,target=None):
            x=NameContextRelationship(f"nctx:{uuid4().hex}",request.name_id,request.runtime_mode,role,state,request.submitter_actor_id,request.approver_actor_id,target,request.source_reference); rel.append(self.contexts.add_relationship(x))
        if request.name_kind in {"first_name","middle_name"}:
            add(NameContextRole.FIRST_NAME_LANGUAGE if request.name_kind=="first_name" else NameContextRole.MIDDLE_NAME_LANGUAGE,ContextState.RESOLVED,request.language_reference_id) if request.language_reference_id else None
            add(NameContextRole.NOT_APPLICABLE_TRIBE,ContextState.NOT_APPLICABLE); add(NameContextRole.NOT_APPLICABLE_ORIGIN,ContextState.NOT_APPLICABLE)
        elif request.classification=="native": add(NameContextRole.NATIVE_SURNAME_TRIBE,ContextState.RESOLVED,request.tribe_reference_id); add(NameContextRole.NOT_APPLICABLE_ORIGIN,ContextState.NOT_APPLICABLE)
        else: add(NameContextRole.SURNAME_ORIGIN,ContextState.RESOLVED,request.origin_reference_id); add(NameContextRole.SURNAME_LANGUAGE,ContextState.RESOLVED,request.language_reference_id)
        return p,tuple(rel)
    def readiness(self,name_id):
        p=self.contexts.get_profile_by_name(name_id); rel=self.contexts.list_relationships(name_id)
        return bool(p and rel and all(x.state in {ContextState.RESOLVED,ContextState.NOT_APPLICABLE} for x in rel))
__all__=["NameProductionContextService"]
