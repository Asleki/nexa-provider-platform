from dataclasses import dataclass
from enum import Enum
class RuntimeMode(str,Enum): production="production"; simulation="simulation"; shared_reference="shared_reference"
class DatasetVisibility(str,Enum): public="public"; internal="internal"; restricted="restricted"; confidential="confidential"
class DatasetLifecycle(str,Enum): candidate="candidate"; validated="validated"; qualified="qualified"; approved="approved"; active="active"; superseded="superseded"; quarantined="quarantined"; rejected="rejected"
@dataclass(frozen=True,slots=True)
class DatasetIdentity:
    dataset_id:str; version:int
    def __post_init__(self):
        if not self.dataset_id or ":" not in self.dataset_id: raise ValueError("dataset_id must be namespaced")
        if self.version<1: raise ValueError("dataset version must be positive")
