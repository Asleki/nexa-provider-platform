from dataclasses import dataclass
from typing import Mapping
@dataclass(frozen=True,slots=True)
class DatabaseRuntimeSettings:
    host:str; port:int; database_name:str; username:str; password:str; ssl_mode:str="require"; min_pool_size:int=1; max_pool_size:int=5; acquisition_timeout_seconds:float=10
    def __post_init__(self):
        if not self.host.strip(): raise ValueError("database host is required")
        if not 1<=self.port<=65535: raise ValueError("database port is invalid")
        if not self.database_name.strip() or not self.username.strip() or not self.password: raise ValueError("database identity and password are required")
        if self.ssl_mode not in {"require","verify-ca","verify-full"}: raise ValueError("unsafe database SSL mode")
        if not 0<=self.min_pool_size<=self.max_pool_size: raise ValueError("invalid pool bounds")
    @classmethod
    def from_mapping(cls,env:Mapping[str,str]):
        return cls(host=env.get("PGHOST",""),port=int(env.get("PGPORT","5432")),database_name=env.get("PGDATABASE",""),username=env.get("PGUSER",""),password=env.get("PGPASSWORD",""),ssl_mode=env.get("PGSSLMODE","require"),min_pool_size=int(env.get("INFRA_DB_POOL_MIN","1")),max_pool_size=int(env.get("INFRA_DB_POOL_MAX","5")),acquisition_timeout_seconds=float(env.get("INFRA_DB_ACQUIRE_TIMEOUT","10")))
    def safe_summary(self): return {"host":self.host,"port":self.port,"databaseName":self.database_name,"username":self.username,"sslMode":self.ssl_mode,"minPoolSize":self.min_pool_size,"maxPoolSize":self.max_pool_size}
