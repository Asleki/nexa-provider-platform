import hashlib,json
from uuid import uuid4
from .contracts import CandidateEnvelope,IngestionReceipt,RejectedCandidate,SourceDescriptor
class DatasetIngestionPipeline:
    def __init__(self,readers,max_bytes=5_000_000): self.readers=tuple(readers); self.max_bytes=max_bytes
    def ingest(self,*,source_package_id,source_file_id,filename,media_type,data,ingestion_run_id=None):
        if len(data)>self.max_bytes: raise ValueError("source exceeds ingestion size limit")
        reader=next((r for r in self.readers if media_type in r.media_types),None)
        if reader is None: raise ValueError("unsupported source media type")
        digest=hashlib.sha256(data).hexdigest(); source=SourceDescriptor(source_package_id,source_file_id,media_type,filename,len(data),digest)
        rejected=[]; candidates=[]
        try: rows=reader.read(data)
        except Exception as exc: rows=[]; rejected.append(RejectedCandidate(0,"SOURCE_PARSE_FAILED",str(exc)))
        for seq,row in enumerate(rows,1): candidates.append(CandidateEnvelope(f"candidate:{digest[:16]}:{seq}",seq,source_file_id,row,{"mediaType":media_type}))
        run=ingestion_run_id or f"ingestion:{uuid4().hex}"
        canonical=json.dumps({"run":run,"source":digest,"candidateIds":[c.candidate_id for c in candidates],"rejected":[r.code for r in rejected]},sort_keys=True,separators=(",",":"))
        return IngestionReceipt(run,source,tuple(candidates),tuple(rejected),hashlib.sha256(canonical.encode()).hexdigest())
