"""Public configuration boundary for an AWS-hosted PWA."""
from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class NameAuthorityPwaRuntimeConfig:
    api_base_url:str; api_version:str="v1"; frontend_origin:str="https://www.nexilabs.online"; offline_contract_version:int=1
    def __post_init__(self):
        if not self.api_base_url.startswith("https://"): raise ValueError("api_base_url must use HTTPS.")
        forbidden=("postgresql://","NPP_POSTGRES_",":5432","rds.amazonaws.com")
        text="|".join((self.api_base_url,self.frontend_origin,self.api_version))
        if any(x in text for x in forbidden): raise ValueError("public PWA configuration contains database connection material.")
    def as_public_dict(self): return {"apiBaseUrl":self.api_base_url,"apiVersion":self.api_version,"frontendOrigin":self.frontend_origin,"offlineContractVersion":self.offline_contract_version}
