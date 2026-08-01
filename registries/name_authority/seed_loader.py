"""Manifest discovery, safe-path enforcement, and seed integrity validation."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from .errors import SeedManifestError,SeedPathError,SeedIntegrityError,SeedRuntimeError
from .models import SeedFileContract,SeedManifest,SeedRow,SeedFileValidation,SeedPackageValidation

class ProductionSeedLoader:
    SCHEMA="npp.production-seed-manifest"
    def __init__(self, seed_root: str|Path): self.seed_root=Path(seed_root).resolve()
    def _safe(self, relative: str)->Path:
        p=Path(relative)
        if p.is_absolute(): raise SeedPathError("absolute seed paths are prohibited.")
        resolved=(self.seed_root/p).resolve()
        if resolved!=self.seed_root and self.seed_root not in resolved.parents: raise SeedPathError("seed path escapes database/seeds.")
        if not resolved.is_file(): raise SeedIntegrityError(f"seed file is missing: {relative}")
        return resolved
    def load_manifest(self, manifest_path: str|Path)->SeedManifest:
        mp=Path(manifest_path).resolve()
        if mp!=self.seed_root and self.seed_root not in mp.parents: raise SeedPathError("manifest is outside the seed root.")
        try: data=json.loads(mp.read_text(encoding="utf-8"))
        except Exception as exc: raise SeedManifestError(f"cannot read manifest: {exc}") from exc
        required={"manifest_schema","manifest_schema_version","classification","status","encoding","delimiter","runtime_policy","governance","dataset_id","dataset_version","dataset_name","domain","source_family","files"}
        missing=required-set(data)
        if missing: raise SeedManifestError(f"manifest is missing fields: {', '.join(sorted(missing))}")
        if data["manifest_schema"]!=self.SCHEMA or data["manifest_schema_version"]!=1: raise SeedManifestError("unsupported production seed manifest schema.")
        if data["classification"]!="production_seed" or data["status"]!="approved": raise SeedManifestError("dataset is not an approved production seed.")
        gov=data["governance"]
        if gov.get("direct_sql_import_allowed") or gov.get("postgresql_copy_allowed") or not gov.get("python_validation_required"): raise SeedManifestError("manifest violates Python-owned import governance.")
        files=[]
        for f in data["files"]:
            files.append(SeedFileContract(f["file_id"],f["path"],f["record_role"],tuple(f["required_headers"]),int(f["row_count"]),f["sha256"],bool(f["import_enabled"]),f.get("target_name_kind"),f.get("column_mappings",{})))
        rp=data["runtime_policy"]
        return SeedManifest(mp,data["dataset_id"],int(data["dataset_version"]),data["dataset_name"],data["domain"],data["source_family"],data["status"],data["encoding"],data["delimiter"],tuple(rp["eligible_runtime_modes"]),tuple(files),data)
    def validate_runtime(self, manifest:SeedManifest, runtime_mode:str)->str:
        if not isinstance(runtime_mode,str): raise SeedRuntimeError("runtime mode must be text.")
        runtime=runtime_mode.strip().lower()
        if runtime not in manifest.eligible_runtime_modes or runtime not in {"simulation","production"}: raise SeedRuntimeError(f"runtime is not eligible: {runtime}")
        return runtime
    def validate(self, manifest:SeedManifest)->SeedPackageValidation:
        out=[]
        for contract in manifest.files:
            path=self._safe(contract.path); raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
            if digest!=contract.sha256: raise SeedIntegrityError(f"checksum mismatch for {contract.file_id}.")
            try:
                with path.open("r",encoding="utf-8-sig",newline="") as fh:
                    reader=csv.reader(fh,delimiter=manifest.delimiter); headers=tuple(next(reader)); rows=sum(1 for _ in reader)
            except UnicodeDecodeError as exc: raise SeedIntegrityError(f"invalid UTF-8 in {contract.file_id}.") from exc
            except StopIteration: headers=(); rows=0
            if headers!=contract.required_headers: raise SeedIntegrityError(f"header mismatch for {contract.file_id}.")
            if rows!=contract.row_count: raise SeedIntegrityError(f"row-count mismatch for {contract.file_id}: expected {contract.row_count}, got {rows}.")
            out.append(SeedFileValidation(contract.file_id,contract.path,rows,digest,headers))
        return SeedPackageValidation(manifest,tuple(out))
    def rows(self, manifest:SeedManifest, contract:SeedFileContract)->tuple[SeedRow,...]:
        path=self._safe(contract.path)
        with path.open("r",encoding="utf-8-sig",newline="") as fh:
            reader=csv.DictReader(fh,delimiter=manifest.delimiter)
            if tuple(reader.fieldnames or ())!=contract.required_headers: raise SeedIntegrityError(f"header mismatch for {contract.file_id}.")
            return tuple(SeedRow(contract,i,row) for i,row in enumerate(reader,start=2))
__all__=["ProductionSeedLoader"]
