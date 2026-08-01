"""Immutable executable production-seed contracts for M009.12 Bundle A."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping

@dataclass(frozen=True, slots=True)
class SeedFileContract:
    file_id: str; path: str; record_role: str; required_headers: tuple[str,...]; row_count: int; sha256: str
    import_enabled: bool; target_name_kind: str|None=None; column_mappings: Mapping[str,str]=None
    def __post_init__(self):
        if not self.file_id or not self.path or not self.record_role: raise ValueError("seed file identity, path, and role are required.")
        if self.row_count < 0 or len(self.sha256)!=64: raise ValueError("seed file row_count or sha256 is invalid.")
        object.__setattr__(self,"required_headers",tuple(self.required_headers))
        object.__setattr__(self,"column_mappings",MappingProxyType(dict(self.column_mappings or {})))

@dataclass(frozen=True, slots=True)
class SeedManifest:
    manifest_path: Path; dataset_id: str; dataset_version: int; dataset_name: str; domain: str; source_family: str
    status: str; encoding: str; delimiter: str; eligible_runtime_modes: tuple[str,...]; files: tuple[SeedFileContract,...]
    raw: Mapping[str,object]
    def __post_init__(self):
        object.__setattr__(self,"eligible_runtime_modes",tuple(self.eligible_runtime_modes))
        object.__setattr__(self,"files",tuple(self.files)); object.__setattr__(self,"raw",MappingProxyType(dict(self.raw)))

@dataclass(frozen=True, slots=True)
class SeedRow:
    file: SeedFileContract; row_number: int; values: Mapping[str,str]
    def __post_init__(self): object.__setattr__(self,"values",MappingProxyType(dict(self.values)))

@dataclass(frozen=True, slots=True)
class SeedFileValidation:
    file_id: str; path: str; row_count: int; sha256: str; headers: tuple[str,...]

@dataclass(frozen=True, slots=True)
class SeedPackageValidation:
    manifest: SeedManifest; files: tuple[SeedFileValidation,...]

@dataclass(frozen=True, slots=True)
class GovernedImportReport:
    operation_id: str; dataset_id: str; runtime_mode: str; candidate_count: int; validated_count: int
    quarantined_count: int; rejected_count: int; imported_count: int; existing_count: int; failed_count: int
    batch_ids: tuple[str,...]
    @property
    def complete(self)->bool: return self.failed_count==0 and self.rejected_count==0
__all__=["SeedFileContract","SeedManifest","SeedRow","SeedFileValidation","SeedPackageValidation","GovernedImportReport"]
