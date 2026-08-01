"""Durable-port and memory implementation for command idempotency."""
from threading import RLock
class MemoryApplicationReceiptRepository:
    def __init__(self): self._d={}; self._lock=RLock()
    def get(self,key): return self._d.get(key)
    def add(self,receipt):
        with self._lock:
            old=self._d.get(receipt.idempotency_key)
            if old and old.request_hash!=receipt.request_hash: raise ValueError("idempotency key was reused with a different payload.")
            if old:return old
            self._d[receipt.idempotency_key]=receipt; return receipt
