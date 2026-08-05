import hashlib,json
from dataclasses import dataclass,field
from typing import Any
class PublicationNotFound(LookupError): pass
@dataclass(frozen=True,slots=True)
class PublicationRecord:
    publication_id:str; dataset_id:str; dataset_version:int; title:str; runtime_mode:str; visibility:str; lifecycle_status:str; payload:dict[str,Any]=field(default_factory=dict); cache_control:str="public, max-age=300"
    def __post_init__(self):
        if self.visibility!="public": raise ValueError("only public records can use the public publication contract")
        if self.lifecycle_status not in {"approved","active"}: raise ValueError("publication requires approved or active lifecycle")
    @property
    def content_sha256(self): return hashlib.sha256(json.dumps(self.payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    @property
    def etag(self): return f'"sha256:{self.content_sha256}"'
    def to_public_dict(self): return {"publicationId":self.publication_id,"datasetId":self.dataset_id,"datasetVersion":self.dataset_version,"title":self.title,"runtimeMode":self.runtime_mode,"contentSha256":self.content_sha256,"payload":self.payload}
