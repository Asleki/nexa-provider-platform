"""Actual PostgreSQL target and TLS verification."""
from __future__ import annotations
from dataclasses import dataclass
from .connection import MigrationDatabaseTarget
from .errors import MigrationTargetError, MigrationTLSRequiredError
@dataclass(frozen=True,slots=True)
class ActualDatabaseTarget:
    database_name:str; current_user:str; session_user:str; server_address:str|None; server_port:int|None; ssl_enabled:bool; server_version:str
class MigrationTargetVerifier:
    def verify(self,expected:MigrationDatabaseTarget,actual:ActualDatabaseTarget)->ActualDatabaseTarget:
        if actual.database_name!=expected.database_name: raise MigrationTargetError(f"Connected database is not the expected target '{expected.database_name}'.")
        if expected.ssl_mode in {'require','verify-ca','verify-full'} and not actual.ssl_enabled: raise MigrationTLSRequiredError("PostgreSQL TLS is required.")
        return actual
