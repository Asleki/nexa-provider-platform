from __future__ import annotations
from abc import ABC,abstractmethod
from threading import RLock
from .name_sync_models import NameSyncReceipt
class NameSyncReceiptRepository(ABC):
    @abstractmethod
    def get_by_request_id(self,request_id:str)->NameSyncReceipt|None: ...
    @abstractmethod
    def save(self,receipt:NameSyncReceipt)->NameSyncReceipt: ...
class MemoryNameSyncReceiptRepository(NameSyncReceiptRepository):
    def __init__(self): self._values={}; self._lock=RLock()
    def get_by_request_id(self,request_id):
        with self._lock: return self._values.get(request_id)
    def save(self,receipt):
        if not isinstance(receipt,NameSyncReceipt): raise TypeError("receipt must be NameSyncReceipt.")
        with self._lock:
            existing=self._values.get(receipt.request_id)
            if existing is not None and existing!=receipt: raise ValueError("request_id already has a different receipt.")
            self._values[receipt.request_id]=receipt
        return receipt
