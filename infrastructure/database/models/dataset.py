from dataclasses import dataclass,field
from typing import Any
@dataclass(frozen=True,slots=True)
class GovernedDatasetRecord:
    dataset_id:str; version:int; title:str; runtime_mode:str; visibility:str; lifecycle_status:str; content_sha256:str; payload:dict[str,Any]=field(default_factory=dict)
