class InMemoryPublicationRepository:
    def __init__(self,records=()): self._records={r.publication_id:r for r in records}
    def save(self,record): self._records[record.publication_id]=record
    def get(self,publication_id): return self._records.get(publication_id)
    def list(self): return tuple(sorted(self._records.values(),key=lambda r:r.publication_id))
