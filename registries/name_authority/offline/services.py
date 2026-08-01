"""Scoped snapshot and acknowledgement services."""
from __future__ import annotations
import hashlib
from .contracts import *
class NameAuthorityOfflineService:
    def __init__(self,read_repository,offline_repository,page_size=100): self.read=read_repository; self.repo=offline_repository; self.page_size=page_size
    def create_snapshot(self,context,scope):
        from registries.name_authority.read_models import NameAuthoritySearchQuery
        limit=min(int(scope.get("limit",self.page_size)),200)
        q=NameAuthoritySearchQuery(runtime_mode=context.authority_runtime,text=str(scope.get("text","")),limit=limit)
        result=self.read.search(q); rows=tuple({"authority_name_id":x.authority_name_id,"runtime_mode":x.runtime_mode,"display_name":x.display_name,"composition":x.composition.value,"status":x.status.value,"read_model_version":x.read_model_version} for x in result.items)
        page_checksum=checksum_records(rows); snapshot_id="namesnapshot:"+hashlib.sha256(f"{context.authority_runtime}|{page_checksum}".encode()).hexdigest()[:32]
        page=NameAuthoritySnapshotPage(snapshot_id,1,rows,len(rows),page_checksum)
        manifest=NameAuthoritySnapshotManifest(snapshot_id,context.authority_runtime,dict(scope),result.read_model_version,1,len(rows),1,page_checksum)
        return {"manifest":manifest,"pages":(page,)}
    def acknowledge(self,receipt):
        old=self.repo.get_receipt(receipt.receipt_id)
        if old:
            if old.checksum!=receipt.checksum: raise ValueError("sync receipt checksum conflict.")
            return old
        return self.repo.add_receipt(receipt)
