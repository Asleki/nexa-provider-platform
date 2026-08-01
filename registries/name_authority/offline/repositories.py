from threading import RLock
class MemoryOfflineRepository:
    def __init__(self): self.drafts={}; self.queue={}; self.receipts={}; self._lock=RLock()
    def save_draft(self,d): self.drafts[(d.partition.actor_id,d.partition.device_id,d.partition.runtime_mode,d.draft_id)]=d; return d
    def enqueue(self,c): self.queue[(c.partition.actor_id,c.partition.device_id,c.partition.runtime_mode,c.queue_item_id)]=c; return c
    def add_receipt(self,r): self.receipts[r.receipt_id]=r; return r
    def get_receipt(self,i): return self.receipts.get(i)
