"""Idempotent offline name catalogue snapshot and delta application service."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime
from typing import Callable
from registries.name_cache import NameCacheEntry,NameCacheState,NameCacheStatus,NameCacheRepository
from .name_sync_models import *
from .name_sync_receipt_repository import NameSyncReceiptRepository
class NameSyncService:
    def __init__(self,cache:NameCacheRepository,receipts:NameSyncReceiptRepository,clock:Callable[[],datetime],receipt_id_factory:Callable[[],str],supported_schema_version:int=1):
        self._cache=cache; self._receipts=receipts; self._clock=clock; self._ids=receipt_id_factory; self._schema=supported_schema_version
    def _existing(self,request):
        existing=self._receipts.get_by_request_id(request.request_id)
        if existing is not None and existing.runtime_mode!=request.runtime_mode: raise ValueError("request runtime conflicts with existing receipt.")
        return existing
    def _receipt(self,request,status,start,end,items):
        return self._receipts.save(NameSyncReceipt(self._ids(),request.request_id,request.runtime_mode,status,self._clock(),start,end,tuple(items)))
    def apply_snapshot(self,request:NameSyncRequest,snapshot:NameCatalogueSnapshot)->NameSyncReceipt:
        if request.operation is not NameSyncOperation.APPLY_SNAPSHOT: raise ValueError("request operation mismatch.")
        existing=self._existing(request)
        if existing is not None: return existing
        start=self._cache.get_state().checkpoint
        if request.runtime_mode!=self._cache.runtime_mode or snapshot.runtime_mode!=self._cache.runtime_mode: return self._receipt(request,NameSyncStatus.REJECTED,start,start,(NameSyncItemResult(snapshot.snapshot_id,NameSyncItemOutcome.REJECTED,message="runtime mismatch"),))
        if snapshot.schema_version!=self._schema: return self._receipt(request,NameSyncStatus.REJECTED,start,start,(NameSyncItemResult(snapshot.snapshot_id,NameSyncItemOutcome.REJECTED,message="schema mismatch"),))
        state=NameCacheState(self._cache.runtime_mode,NameCacheStatus.READY,snapshot.schema_version,snapshot.catalogue_version,snapshot.checkpoint,len(snapshot.entries),self._clock())
        self._cache.replace_snapshot(snapshot.entries,state)
        items=tuple(NameSyncItemResult(e.record.name_id,NameSyncItemOutcome.APPLIED,e.record.name_id) for e in snapshot.entries)
        return self._receipt(request,NameSyncStatus.COMPLETED,start,snapshot.checkpoint,items)
    def apply_change_set(self,request:NameSyncRequest,change_set:NameCatalogueChangeSet)->NameSyncReceipt:
        if request.operation is not NameSyncOperation.APPLY_CHANGE_SET: raise ValueError("request operation mismatch.")
        existing=self._existing(request)
        if existing is not None: return existing
        state=self._cache.get_state(); start=state.checkpoint
        if request.runtime_mode!=self._cache.runtime_mode or change_set.runtime_mode!=self._cache.runtime_mode: return self._receipt(request,NameSyncStatus.REJECTED,start,start,(NameSyncItemResult(change_set.change_set_id,NameSyncItemOutcome.REJECTED,message="runtime mismatch"),))
        if change_set.schema_version!=self._schema: return self._receipt(request,NameSyncStatus.REJECTED,start,start,(NameSyncItemResult(change_set.change_set_id,NameSyncItemOutcome.REJECTED,message="schema mismatch"),))
        if start!=change_set.starting_checkpoint: return self._receipt(request,NameSyncStatus.REJECTED,start,start,(NameSyncItemResult(change_set.change_set_id,NameSyncItemOutcome.REJECTED,message="checkpoint mismatch"),))
        upserts=[]; removals=[]; items=[]; existing_count=state.entry_count
        for c in change_set.changes:
            if c.change_type is NameChangeType.UPSERT:
                upserts.append(c.entry); items.append(NameSyncItemResult(c.change_id,NameSyncItemOutcome.APPLIED,c.canonical_name_id))
            else:
                try: self._cache.get(c.canonical_name_id); exists=True
                except Exception: exists=False
                removals.append(c.canonical_name_id); items.append(NameSyncItemResult(c.change_id,NameSyncItemOutcome.APPLIED if exists else NameSyncItemOutcome.SKIPPED,c.canonical_name_id,"removed" if exists else "not cached"))
        current_ids={r.name_id for r in self._cache.search(__import__('registries.names.name_search_query',fromlist=['NameSearchQuery']).NameSearchQuery(runtime_mode=self._cache.runtime_mode,status=None,limit=1000)).records}
        final_ids=(current_ids-set(removals))|{e.record.name_id for e in upserts}
        new_state=NameCacheState(self._cache.runtime_mode,NameCacheStatus.READY,change_set.schema_version,change_set.catalogue_version,change_set.ending_checkpoint,len(final_ids),self._clock())
        self._cache.apply_changes(tuple(upserts),tuple(removals),new_state)
        status=NameSyncStatus.COMPLETED
        return self._receipt(request,status,start,change_set.ending_checkpoint,items)
