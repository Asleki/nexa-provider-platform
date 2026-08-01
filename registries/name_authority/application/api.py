"""Thin transport-neutral API dispatcher."""
from .contracts import NameAuthorityOperation
class NameAuthorityApplicationApi:
    def __init__(self,service): self.service=service
    def execute(self,operation,context,**payload):
        op=operation if isinstance(operation,NameAuthorityOperation) else NameAuthorityOperation(operation)
        fn={NameAuthorityOperation.SEARCH:self.service.search,NameAuthorityOperation.GET:self.service.get,NameAuthorityOperation.STATISTICS:self.service.statistics,NameAuthorityOperation.SUBMIT_MANUAL:self.service.submit_manual,NameAuthorityOperation.APPROVE_MANUAL:self.service.approve_manual,NameAuthorityOperation.COMPOSE:self.service.compose,NameAuthorityOperation.SNAPSHOT:self.service.snapshot,NameAuthorityOperation.ACK_SYNC:self.service.acknowledge_sync}.get(op)
        if fn is None: raise ValueError("operation is not implemented.")
        return fn(context,**payload)
