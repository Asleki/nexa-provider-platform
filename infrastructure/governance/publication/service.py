from .contracts import PublicationNotFound
class PublicationService:
    def __init__(self,repository): self.repository=repository
    def publish(self,record): self.repository.save(record); return record
    def list_public(self): return tuple(r for r in self.repository.list() if r.visibility=="public" and r.lifecycle_status in {"approved","active"})
    def get_public(self,publication_id):
        record=self.repository.get(publication_id)
        if record is None or record.visibility!="public" or record.lifecycle_status not in {"approved","active"}: raise PublicationNotFound(publication_id)
        return record
