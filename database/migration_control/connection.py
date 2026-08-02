"""Password-free PostgreSQL connection configuration and lazy driver loading."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Any
from shared.runtime.runtime_config import RuntimeEnvironment
from .constants import DEFAULT_CONNECT_TIMEOUT, DEFAULT_POSTGRESQL_PORT, SUPPORTED_SSL_MODES
from .errors import MigrationConfigurationError
@dataclass(frozen=True,slots=True)
class MigrationDatabaseTarget:
    host:str; database_name:str; username:str; environment:RuntimeEnvironment
    port:int=DEFAULT_POSTGRESQL_PORT; ssl_mode:str="require"; connect_timeout:int=DEFAULT_CONNECT_TIMEOUT
    def __post_init__(self):
        for n in ('host','database_name','username'):
            if not isinstance(getattr(self,n),str) or not getattr(self,n).strip(): raise MigrationConfigurationError(f"{n} is required.")
        if not isinstance(self.port,int) or not 1<=self.port<=65535: raise MigrationConfigurationError("port is invalid.")
        if self.ssl_mode not in SUPPORTED_SSL_MODES: raise MigrationConfigurationError("unsupported ssl_mode.")
        if not isinstance(self.connect_timeout,int) or self.connect_timeout<1: raise MigrationConfigurationError("connect_timeout must be positive.")
    @classmethod
    def from_environment(cls,source:Mapping[str,str]):
        try: env=RuntimeEnvironment(source.get('NPP_ENVIRONMENT','development').strip().lower())
        except ValueError as e: raise MigrationConfigurationError("NPP_ENVIRONMENT is unsupported.") from e
        return cls(host=source.get('PGHOST',''),port=int(source.get('PGPORT','5432')),database_name=source.get('PGDATABASE',''),username=source.get('PGUSER',''),environment=env,ssl_mode=source.get('PGSSLMODE','require'),connect_timeout=int(source.get('PGCONNECT_TIMEOUT','10')))
def build_psycopg_connection_factory(target:MigrationDatabaseTarget,password:str)->Callable[[],Any]:
    if not isinstance(password,str) or not password: raise MigrationConfigurationError("database password is required.")
    def factory():
        try: import psycopg
        except ImportError as e: raise MigrationConfigurationError("Python package 'psycopg' is required for live PostgreSQL migration commands.") from e
        return psycopg.connect(host=target.host,port=target.port,dbname=target.database_name,user=target.username,password=password,sslmode=target.ssl_mode,connect_timeout=target.connect_timeout)
    return factory
