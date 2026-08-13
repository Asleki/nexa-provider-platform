"""P006.7.1.9 deterministic Country Registry read model."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
import hashlib,json
from .persistence import CountryRegistryRecord

@dataclass(frozen=True,slots=True)
class CountryReadModel:
    country_id:str; official_name:str; short_name:str; alpha2_code:str; alpha3_code:str; sovereignty_status:str; lifecycle_status:str; record_version:int; boundary_id:str; boundary_version:int; realm_id:str; timezone_code:str; calendar_code:str; date_time_policy_id:str; currency_code:str; currency_symbol:str; read_model_version:int=1; projected_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self):
        if not self.country_id.startswith("country:"): raise ValueError("country_id must use country: namespace.")
        if self.record_version<1 or self.read_model_version<1: raise ValueError("versions must be positive.")
        if self.projected_at.tzinfo is None: raise ValueError("projected_at must be timezone-aware.")
        object.__setattr__(self,"projected_at",self.projected_at.astimezone(timezone.utc))
    def semantic_dict(self):
        return {k:getattr(self,k) for k in ("country_id","official_name","short_name","alpha2_code","alpha3_code","sovereignty_status","lifecycle_status","record_version","boundary_id","boundary_version","realm_id","timezone_code","calendar_code","date_time_policy_id","currency_code","currency_symbol","read_model_version")}
    @property
    def checksum(self): return hashlib.sha256(json.dumps(self.semantic_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CountryProjectionReceipt:
    country_id:str; source_record_version:int; read_model_version:int; checksum:str

class CountryReadModelProjector:
    def project(self,record:CountryRegistryRecord,*,read_model_version:int=1,projected_at:datetime|None=None):
        if not isinstance(record,CountryRegistryRecord): raise TypeError("record must be CountryRegistryRecord.")
        i=record.identity
        return CountryReadModel(record.country_id,i.official_name,i.short_name,record.alpha2_code,record.alpha3_code,i.sovereignty_status.value,i.status.value,i.record_version,record.boundary_id,record.boundary_version,record.realm_id,record.timezone_code,record.calendar_code,record.date_time_policy_id,record.currency_code,record.currency_symbol,read_model_version,projected_at or datetime.now(timezone.utc))
    def rebuild(self,records,repository,*,read_model_version=1):
        receipts=[]
        for r in sorted(tuple(records),key=lambda x:x.country_id):
            m=self.project(r,read_model_version=read_model_version); repository.upsert(m); receipts.append(CountryProjectionReceipt(m.country_id,m.record_version,m.read_model_version,m.checksum))
        return tuple(receipts)

class MemoryCountryReadRepository:
    def __init__(self): self._records={}
    def upsert(self,model):
        if not isinstance(model,CountryReadModel): raise TypeError("model must be CountryReadModel.")
        self._records[model.country_id]=model; return model
    def get(self,country_id):
        key=str(country_id).strip().lower()
        try:return self._records[key]
        except KeyError as exc: raise KeyError("country read model was not found.") from exc
    def list_all(self): return tuple(self._records[k] for k in sorted(self._records))

__all__=["CountryReadModel","CountryProjectionReceipt","CountryReadModelProjector","MemoryCountryReadRepository"]
