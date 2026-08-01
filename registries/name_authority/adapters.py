"""Manifest-driven source adapters producing existing immutable NameCandidate values."""
from __future__ import annotations
import hashlib
from datetime import datetime,timezone
from registries.name_imports.name_candidate import NameCandidate
from registries.name_imports.name_candidate_status import NameCandidateStatus
from registries.names.name_kind import NameKind
from registries.names.name_sex_usage import NameSexUsage
from .errors import SeedAdapterError,SeedRelationshipError,SeedSourceNotAtomicError
from .models import SeedManifest,SeedRow

def _slug(value:str)->str: return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
def _sex(value:str|None)->NameSexUsage:
    key=(value or "unspecified").strip().lower()
    mapping={"male":NameSexUsage.MALE,"female":NameSexUsage.FEMALE,"unisex":NameSexUsage.UNISEX,"unspecified":NameSexUsage.UNSPECIFIED,"":NameSexUsage.UNSPECIFIED}
    if key not in mapping: raise SeedAdapterError(f"unsupported sex usage: {value!r}")
    return mapping[key]

class ProductionSeedAdapter:
    VERSION=1
    def __init__(self, manifest:SeedManifest, runtime_mode:str, *, tribe_ids:frozenset[str]=frozenset(), clock=lambda:datetime.now(timezone.utc)):
        self.manifest=manifest; self.runtime=runtime_mode; self.tribe_ids=tribe_ids; self.clock=clock
    def adapt(self,row:SeedRow,batch_id:str)->tuple[NameCandidate,...]:
        f=row.file; values=row.values
        if not f.import_enabled: raise SeedSourceNotAtomicError(f"{f.file_id} is not enabled for atomic-name import.")
        base={"dataset_id":self.manifest.dataset_id,"dataset_version":self.manifest.dataset_version,"file_id":f.file_id,"source_family":self.manifest.source_family,"source_record_id":None,"adapter_version":self.VERSION}
        if f.record_role=="paired_full_name_source":
            sid=values["id"].strip(); origin=values["origin"].strip(); language=values["language"].strip()
            return (self._candidate(row,batch_id,sid+":first",values["first_name"],NameKind.FIRST_NAME,NameSexUsage.UNSPECIFIED,{**base,"source_record_id":sid,"source_pair_id":sid,"component_role":"first_name","origin_label":origin,"language_label":language}),self._candidate(row,batch_id,sid+":surname",values["second_name"],NameKind.SURNAME,NameSexUsage.UNSPECIFIED,{**base,"source_record_id":sid,"source_pair_id":sid,"component_role":"surname","origin_label":origin,"language_label":language}))
        if f.record_role!="atomic_name": raise SeedSourceNotAtomicError(f"{f.file_id} is not an atomic-name source.")
        kind=NameKind.parse(f.target_name_kind); source_col=next((k for k,v in f.column_mappings.items() if v=="raw_name_value"),None)
        id_col=next((k for k,v in f.column_mappings.items() if v=="external_record_id"),None)
        if not source_col or not id_col: raise SeedAdapterError(f"manifest mappings are incomplete for {f.file_id}.")
        sid=values[id_col].strip(); attrs={**base,"source_record_id":sid}
        sex=NameSexUsage.UNSPECIFIED; culture_refs=()
        for key,target in f.column_mappings.items():
            val=values.get(key,"").strip()
            if target=="sex_usage": sex=_sex(val)
            elif target=="attributes.source_origin": attrs["origin_label"]=val; attrs["reference_state"]="unresolved"
            elif target=="attributes.source_language": attrs["language_label"]=val; attrs["reference_state"]="unresolved"
            elif target=="culture_refs[0]":
                if val not in self.tribe_ids: raise SeedRelationshipError(f"unknown tribe reference {val!r} at row {row.row_number}.")
                culture_refs=(val,); attrs["tribe_reference_state"]="seed_reference_reserved"
        return (self._candidate(row,batch_id,sid,values[source_col],kind,sex,attrs,culture_refs),)
    def _candidate(self,row,batch_id,external_id,value,kind,sex,attrs,culture_refs=()):
        identity=f"{self.manifest.dataset_id}|{row.file.file_id}|{external_id}|{self.runtime}"
        return NameCandidate("namecandidate:"+_slug(identity),batch_id,row.file.file_id,row.row_number,value,kind,self.runtime,sex,self.manifest.dataset_id,external_id,culture_refs=culture_refs,attributes={"seed":attrs},status=NameCandidateStatus.STAGED,created_at=self.clock())

def load_tribe_ids(rows:tuple[SeedRow,...])->frozenset[str]:
    ids=[]
    for row in rows:
        ident=row.values.get("id","").strip()
        if not ident or ident in ids: raise SeedRelationshipError("tribe reference IDs must be non-empty and unique.")
        ids.append(ident)
    return frozenset(ids)
__all__=["ProductionSeedAdapter","load_tribe_ids"]
