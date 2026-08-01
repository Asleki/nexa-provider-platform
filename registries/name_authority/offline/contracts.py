"""IndexedDB-compatible offline contracts for Name Authority."""
from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from enum import Enum
import hashlib,json
class OfflineOperationPolicy(str,Enum): OFFLINE_ALLOWED="offline_allowed"; OFFLINE_DRAFT_ONLY="offline_draft_only"; OFFLINE_QUEUE_ALLOWED="offline_queue_allowed"; ONLINE_REQUIRED="online_required"; ADMIN_ONLINE_REQUIRED="admin_online_required"
class OfflineQueueStatus(str,Enum): DRAFT="draft"; QUEUED="queued"; SUBMITTING="submitting"; ACCEPTED="accepted"; REJECTED="rejected"; CONFLICT="conflict"; QUARANTINED="quarantined"
@dataclass(frozen=True,slots=True)
class OfflinePartition: actor_id:str; device_id:str; runtime_mode:str
@dataclass(frozen=True,slots=True)
class NameAuthorityOfflineDraft:
    draft_id:str; partition:OfflinePartition; payload:dict; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
@dataclass(frozen=True,slots=True)
class OfflineCommand:
    queue_item_id:str; partition:OfflinePartition; request_id:str; idempotency_key:str; operation:str; payload:dict; local_sequence:int; status:OfflineQueueStatus=OfflineQueueStatus.QUEUED; attempt_count:int=0
@dataclass(frozen=True,slots=True)
class NameAuthoritySnapshotManifest:
    snapshot_id:str; runtime_mode:str; scope:dict; read_model_version:int; schema_version:int; record_count:int; page_count:int; checksum:str; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
@dataclass(frozen=True,slots=True)
class NameAuthoritySnapshotPage:
    snapshot_id:str; page_number:int; records:tuple; record_count:int; page_checksum:str
@dataclass(frozen=True,slots=True)
class NameAuthoritySyncReceipt:
    receipt_id:str; request_id:str; device_id:str; actor_id:str; runtime_mode:str; snapshot_id:str; applied_count:int; failed_count:int; conflict_count:int; checksum:str; completed_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
def checksum_records(records):
    raw=json.dumps(records,sort_keys=True,separators=(",",":"),default=str,ensure_ascii=False); return hashlib.sha256(raw.encode()).hexdigest()
