"""Immutable API settings loaded explicitly from environment mappings."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

_ALLOWED_ENVIRONMENTS={"development","testing","staging","production"}

@dataclass(frozen=True, slots=True)
class InfrastructureSettings:
    application_name:str="Nexa Shared Infrastructure API"
    application_version:str="0.1.0"
    environment_name:str="development"
    api_prefix:str="/api/v1"
    allowed_origins:tuple[str,...]=()
    trusted_hosts:tuple[str,...] = ("localhost","127.0.0.1","testserver")
    docs_enabled:bool=True

    def __post_init__(self):
        if self.environment_name not in _ALLOWED_ENVIRONMENTS: raise ValueError("unsupported infrastructure environment")
        if not self.api_prefix.startswith("/"): raise ValueError("api_prefix must start with '/'")
        if "*" in self.allowed_origins and self.environment_name=="production": raise ValueError("wildcard CORS is forbidden in production")

    @classmethod
    def from_mapping(cls, env:Mapping[str,str]):
        split=lambda key: tuple(v.strip() for v in env.get(key,"").split(",") if v.strip())
        return cls(application_name=env.get("INFRA_APPLICATION_NAME",cls.application_name), application_version=env.get("INFRA_APPLICATION_VERSION",cls.application_version), environment_name=env.get("INFRA_ENVIRONMENT","development"), api_prefix=env.get("INFRA_API_PREFIX","/api/v1"), allowed_origins=split("INFRA_ALLOWED_ORIGINS"), trusted_hosts=split("INFRA_TRUSTED_HOSTS") or cls.trusted_hosts, docs_enabled=env.get("INFRA_DOCS_ENABLED","true").lower() in {"1","true","yes"})
