from dataclasses import dataclass
from enum import Enum
class QualificationDecision(str,Enum): qualified="qualified"; rejected="rejected"; quarantined="quarantined"
@dataclass(frozen=True,slots=True)
class QualificationRequest:
    qualification_id:str; validation_receipt_id:str; submitter_actor_id:str; approver_actor_id:str
    def __post_init__(self):
        if self.submitter_actor_id==self.approver_actor_id: raise ValueError("submitter and approver must be different")
@dataclass(frozen=True,slots=True)
class QualificationReceipt:
    qualification_id:str; validation_receipt_id:str; decision:QualificationDecision; reason:str
