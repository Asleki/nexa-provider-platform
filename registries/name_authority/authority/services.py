"""Authority composition validation and construction."""
from __future__ import annotations
import hashlib
from .contracts import *
from registries.names import NameKind,NameStatus,comparison_key
class AuthorityNameBuilder:
    RULES={
      AuthorityNameComposition.SINGLE_NAME:((AuthorityComponentRole.SINGLE_NAME,),),
      AuthorityNameComposition.FIRST_SURNAME:((AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME),),
      AuthorityNameComposition.FIRST_MIDDLE:((AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.MIDDLE_NAME),),
      AuthorityNameComposition.FIRST_MIDDLE_SURNAME:((AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.MIDDLE_NAME,AuthorityComponentRole.SURNAME),),
      AuthorityNameComposition.INTERNATIONAL_PAIR:((AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME),),
      AuthorityNameComposition.COMPOUND_SURNAME:((AuthorityComponentRole.FIRST_NAME,AuthorityComponentRole.SURNAME),),
    }
    KIND_FOR_ROLE={AuthorityComponentRole.FIRST_NAME:NameKind.FIRST_NAME,AuthorityComponentRole.MIDDLE_NAME:NameKind.MIDDLE_NAME,AuthorityComponentRole.SURNAME:NameKind.SURNAME}
    def build(self,composition,atomic_names,roles,actor_id="system",runtime_mode="production",metadata=None):
        comp=AuthorityNameComposition.parse(composition); names=tuple(atomic_names); roles=tuple(AuthorityComponentRole.parse(r) for r in roles)
        if len(names)!=len(roles): raise ValueError("atomic names and roles must have equal length.")
        expected=self.RULES[comp][0]
        if roles!=expected: raise ValueError("component roles do not match composition.")
        components=[]
        for i,(name,role) in enumerate(zip(names,roles),1):
            if name.metadata.runtime_mode!=runtime_mode: raise ValueError("mixed-runtime authority composition is prohibited.")
            if name.metadata.status is not NameStatus.ACTIVE: raise ValueError("only active atomic names may form a new authority record.")
            expected_kind=self.KIND_FOR_ROLE.get(role)
            if expected_kind and name.name_kind is not expected_kind: raise ValueError("atomic name kind does not match component role.")
            components.append(AuthorityNameComponent(i,name.name_id,name.name_kind,role,name.canonical_value," " if i<len(names) else ""))
        display="".join(c.canonical_value+c.separator_after for c in components)
        raw="|".join([runtime_mode,comp.value]+[f"{c.position}:{c.name_id}:{c.role.value}" for c in components]); key=hashlib.sha256(raw.encode()).hexdigest()
        authority_id="nameauth:"+key[:32]
        return NameAuthorityRecord(authority_id,runtime_mode,comp,tuple(components),display,comparison_key(display),key,created_by_actor_id=actor_id,approved_by_actor_id=actor_id,metadata=metadata or {})
class NameAuthorityService:
    def __init__(self,repository,builder=None): self.repository=repository; self.builder=builder or AuthorityNameBuilder()
    def create_or_get(self,*args,**kwargs): return self.repository.create_or_get(self.builder.build(*args,**kwargs))
