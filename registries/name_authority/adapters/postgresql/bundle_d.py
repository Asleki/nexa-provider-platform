"""PostgreSQL adapters for Bundle D command and sync receipts."""
from __future__ import annotations
import json
from registries.name_authority.application import ApplicationCommandReceipt,ApplicationResponse,ApplicationError,ApplicationErrorCode,NameAuthorityOperation
from registries.name_authority.offline import NameAuthoritySyncReceipt
class PostgreSQLApplicationReceiptRepository:
    def __init__(self,provider): self.provider=provider
    def _run(self,fn):
        c=self.provider.connect()
        try:r=fn(c); c.commit(); return r
        except Exception:c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    def get(self,key):
        def op(c):
            cur=c.cursor(); cur.execute("SELECT idempotency_key,operation,actor_id,runtime_mode,request_hash,response_payload,created_at FROM reference.name_authority_command_receipt WHERE idempotency_key=%s",(key,)); row=cur.fetchone()
            if row is None:return None
            payload=row[5] if isinstance(row[5],dict) else json.loads(row[5]); err=payload.get("error")
            response=ApplicationResponse(payload["ok"],payload["request_id"],payload["correlation_id"],payload["runtime_mode"],payload.get("data"),None if not err else ApplicationError(ApplicationErrorCode(err["code"]),err["message"],err.get("retryable",False),err.get("field_errors",{})))
            return ApplicationCommandReceipt(row[0],NameAuthorityOperation(row[1]),row[2],row[3],row[4],response,row[6])
        return self._run(op)
    def add(self,receipt):
        def op(c):
            cur=c.cursor(); response={"ok":receipt.response.ok,"request_id":receipt.response.request_id,"correlation_id":receipt.response.correlation_id,"runtime_mode":receipt.response.runtime_mode,"data":receipt.response.data if isinstance(receipt.response.data,(dict,list,str,int,float,bool,type(None))) else str(receipt.response.data),"error":None if receipt.response.error is None else {"code":receipt.response.error.code.value,"message":receipt.response.error.message,"retryable":receipt.response.error.retryable,"field_errors":dict(receipt.response.error.field_errors)}}
            cur.execute("INSERT INTO reference.name_authority_command_receipt (idempotency_key,operation,actor_id,runtime_mode,request_hash,response_payload,created_at) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s) ON CONFLICT (idempotency_key) DO NOTHING",(receipt.idempotency_key,receipt.operation.value,receipt.actor_id,receipt.runtime_mode,receipt.request_hash,json.dumps(response,default=str),receipt.created_at)); return receipt
        return self._run(op)
class PostgreSQLSyncReceiptRepository:
    def __init__(self,provider): self.provider=provider
    def add(self,r):
        c=self.provider.connect()
        try:
            cur=c.cursor(); cur.execute("INSERT INTO reference.name_authority_sync_receipt (receipt_id,request_id,device_id,actor_id,runtime_mode,snapshot_id,applied_count,failed_count,conflict_count,checksum,completed_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (receipt_id) DO NOTHING",(r.receipt_id,r.request_id,r.device_id,r.actor_id,r.runtime_mode,r.snapshot_id,r.applied_count,r.failed_count,r.conflict_count,r.checksum,r.completed_at)); c.commit(); return r
        except Exception:c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
