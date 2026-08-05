from dataclasses import dataclass,field
from typing import Any
@dataclass(frozen=True,slots=True)
class SourceDescriptor:
    source_package_id:str; source_file_id:str; media_type:str; filename:str; byte_length:int; content_sha256:str
@dataclass(frozen=True,slots=True)
class CandidateEnvelope:
    candidate_id:str; sequence:int; source_file_id:str; payload:dict[str,Any]; metadata:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True,slots=True)
class RejectedCandidate:
    sequence:int; code:str; message:str
@dataclass(frozen=True,slots=True)
class IngestionReceipt:
    ingestion_run_id:str; source:SourceDescriptor; candidates:tuple[CandidateEnvelope,...]; rejected:tuple[RejectedCandidate,...]; receipt_sha256:str
