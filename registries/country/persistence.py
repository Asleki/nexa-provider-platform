"""P006.7.1.7 canonical Country Registry persistence contracts."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from .contracts import CountryIdentity

class CountryRepositoryError(RuntimeError): pass
class CountryAlreadyExistsError(CountryRepositoryError): pass
class CountryNotFoundError(CountryRepositoryError): pass
class CountryVersionConflictError(CountryRepositoryError): pass

@dataclass(frozen=True, slots=True)
class CountryRegistryRecord:
    identity: CountryIdentity
    alpha2_code: str
    alpha3_code: str
    boundary_id: str
    boundary_version: int
    realm_id: str
    timezone_code: str
    calendar_code: str
    date_time_policy_id: str
    currency_code: str
    currency_symbol: str
    persisted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.identity, CountryIdentity): raise TypeError("identity must be CountryIdentity.")
        for name in ("alpha2_code","alpha3_code","boundary_id","realm_id","timezone_code","calendar_code","date_time_policy_id","currency_code","currency_symbol"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} is required.")
            object.__setattr__(self,name,value.strip())
        if len(self.alpha2_code)!=2 or not self.alpha2_code.isalpha(): raise ValueError("alpha2_code must be two letters.")
        if len(self.alpha3_code)!=3 or not self.alpha3_code.isalpha(): raise ValueError("alpha3_code must be three letters.")
        object.__setattr__(self,"alpha2_code",self.alpha2_code.upper()); object.__setattr__(self,"alpha3_code",self.alpha3_code.upper()); object.__setattr__(self,"currency_code",self.currency_code.upper())
        if self.boundary_version < 1: raise ValueError("boundary_version must be positive.")
        if not isinstance(self.persisted_at,datetime) or self.persisted_at.tzinfo is None: raise ValueError("persisted_at must be timezone-aware.")
        object.__setattr__(self,"persisted_at",self.persisted_at.astimezone(timezone.utc))

    @property
    def country_id(self)->str: return self.identity.country_id
    @property
    def record_version(self)->int: return self.identity.record_version

class CountryRepository(ABC):
    @abstractmethod
    def add(self, record: CountryRegistryRecord) -> CountryRegistryRecord: ...
    @abstractmethod
    def get(self, country_id: str) -> CountryRegistryRecord: ...
    @abstractmethod
    def replace(self, record: CountryRegistryRecord, *, expected_version: int) -> CountryRegistryRecord: ...
    @abstractmethod
    def exists(self, country_id: str) -> bool: ...
    @abstractmethod
    def list_all(self) -> tuple[CountryRegistryRecord,...]: ...

class MemoryCountryRepository(CountryRepository):
    def __init__(self)->None: self._records={}; self._lock=RLock()
    @staticmethod
    def _id(value:str)->str:
        if not isinstance(value,str) or not value.strip(): raise ValueError("country_id is required.")
        return value.strip().lower()
    def add(self,record):
        if not isinstance(record,CountryRegistryRecord): raise TypeError("record must be CountryRegistryRecord.")
        with self._lock:
            if record.country_id in self._records: raise CountryAlreadyExistsError(record.country_id)
            self._records[record.country_id]=record; return record
    def get(self,country_id):
        key=self._id(country_id)
        with self._lock:
            try:return self._records[key]
            except KeyError as exc: raise CountryNotFoundError(key) from exc
    def replace(self,record,*,expected_version):
        if not isinstance(record,CountryRegistryRecord): raise TypeError("record must be CountryRegistryRecord.")
        if not isinstance(expected_version,int) or isinstance(expected_version,bool) or expected_version<1: raise ValueError("expected_version must be positive.")
        with self._lock:
            current=self._records.get(record.country_id)
            if current is None: raise CountryNotFoundError(record.country_id)
            if current.record_version != expected_version: raise CountryVersionConflictError(f"expected {expected_version}, found {current.record_version}.")
            if record.record_version != expected_version+1: raise CountryVersionConflictError("replacement record_version must increment by exactly one.")
            self._records[record.country_id]=record; return record
    def exists(self,country_id):
        with self._lock:return self._id(country_id) in self._records
    def list_all(self):
        with self._lock:return tuple(self._records[k] for k in sorted(self._records))

__all__=["CountryRegistryRecord","CountryRepository","MemoryCountryRepository","CountryRepositoryError","CountryAlreadyExistsError","CountryNotFoundError","CountryVersionConflictError"]
