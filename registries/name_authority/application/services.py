"""Framework-neutral Name Authority query and command services."""
from __future__ import annotations
from dataclasses import asdict
from .contracts import *
from .permissions import *
from registries.name_authority.manual import ActorContext

class NameAuthorityApplicationService:
    def __init__(self,read_repository,name_repository,candidate_repository,manual_service,authority_service,receipt_repository,offline_service=None,authorization=None):
        self.read_repository=read_repository; self.name_repository=name_repository; self.candidate_repository=candidate_repository; self.manual_service=manual_service; self.authority_service=authority_service; self.receipts=receipt_repository; self.offline_service=offline_service; self.auth=authorization or NameAuthorityAuthorization()
    def _ok(self,c,data): return ApplicationResponse(True,c.request_id,c.correlation_id,c.authority_runtime,data=data)
    def _err(self,c,code,msg,retry=False): return ApplicationResponse(False,c.request_id,c.correlation_id,c.authority_runtime,error=ApplicationError(code,msg,retry))
    def _safe(self,c,permission,fn):
        try:self.auth.require(c,permission); return fn()
        except PermissionError as e:
            msg=str(e); code=ApplicationErrorCode.AUTHENTICATION_REQUIRED if "authentication" in msg else ApplicationErrorCode.RUNTIME_ACCESS_DENIED if "runtime" in msg else ApplicationErrorCode.PERMISSION_DENIED
            return self._err(c,code,msg)
        except KeyError:return self._err(c,ApplicationErrorCode.NOT_FOUND,"requested Name Authority resource was not found.")
        except ValueError as e:return self._err(c,ApplicationErrorCode.INVALID_REQUEST,str(e))
        except Exception:return self._err(c,ApplicationErrorCode.INTERNAL_FAILURE,"Name Authority operation failed.",True)
    def search(self,c,query):
        return self._safe(c,SEARCH,lambda:self._ok(c,self.read_repository.search(query)))
    def get(self,c,authority_name_id):
        return self._safe(c,READ,lambda:self._get_checked(c,authority_name_id))
    def _get_checked(self,c,i):
        m=self.read_repository.get(i)
        if m.runtime_mode!=c.authority_runtime: raise PermissionError("runtime access denied")
        return self._ok(c,m)
    def statistics(self,c): return self._safe(c,STATS,lambda:self._ok(c,self.read_repository.statistics(c.authority_runtime)))
    def _idempotent(self,c,operation,payload,fn):
        if not c.idempotency_key: raise ValueError("idempotency_key is required for commands.")
        h=stable_request_hash(operation,payload); old=self.receipts.get(c.idempotency_key)
        if old:
            if old.request_hash!=h: raise ValueError("idempotency key was reused with a different payload.")
            return old.response
        response=fn(); self.receipts.add(ApplicationCommandReceipt(c.idempotency_key,operation,c.principal.actor_id,c.authority_runtime,h,response)); return response
    def submit_manual(self,c,request):
        return self._safe(c,MANUAL_CREATE,lambda:self._idempotent(c,NameAuthorityOperation.SUBMIT_MANUAL,{"request_id":request.request_id,"raw":request.raw_name_value,"kind":request.requested_name_kind.value},lambda:self._ok(c,self.manual_service.submit(request))))
    def approve_manual(self,c,candidate_id,reason="approved"):
        def run():
            candidate=self.candidate_repository.get(candidate_id)
            if candidate.request.actor.actor_id==c.principal.actor_id: return self._err(c,ApplicationErrorCode.SELF_APPROVAL_PROHIBITED,"submitter cannot approve the same candidate.")
            actor=ActorContext(c.principal.actor_id,c.principal.actor_type,device_id=c.principal.device_id,correlation_id=c.correlation_id)
            return self._ok(c,self.manual_service.approve(candidate_id,actor,reason))
        return self._safe(c,MANUAL_APPROVE,lambda:self._idempotent(c,NameAuthorityOperation.APPROVE_MANUAL,{"candidate_id":candidate_id,"reason":reason},run))
    def compose(self,c,composition,atomic_name_ids,roles,metadata=None):
        def run():
            names=tuple(self.name_repository.get(i) for i in atomic_name_ids)
            record=self.authority_service.create_or_get(composition,names,roles,actor_id=c.principal.actor_id,runtime_mode=c.authority_runtime,metadata=metadata or {})
            return self._ok(c,record)
        return self._safe(c,COMPOSE,lambda:self._idempotent(c,NameAuthorityOperation.COMPOSE,{"composition":str(composition),"ids":list(atomic_name_ids),"roles":[str(x) for x in roles]},run))
    def snapshot(self,c,scope=None):
        if self.offline_service is None:return self._err(c,ApplicationErrorCode.INTERNAL_FAILURE,"offline service is unavailable.")
        return self._safe(c,SNAPSHOT_READ,lambda:self._ok(c,self.offline_service.create_snapshot(c,scope or {})))
    def acknowledge_sync(self,c,receipt):
        if self.offline_service is None:return self._err(c,ApplicationErrorCode.INTERNAL_FAILURE,"offline service is unavailable.")
        return self._safe(c,SYNC_ACK,lambda:self._idempotent(c,NameAuthorityOperation.ACK_SYNC,{"receipt_id":receipt.receipt_id,"checksum":receipt.checksum},lambda:self._ok(c,self.offline_service.acknowledge(receipt))))
