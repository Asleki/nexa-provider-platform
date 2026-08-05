from dataclasses import dataclass
from enum import Enum
from typing import Any
class FindingSeverity(str,Enum): info="info"; warning="warning"; error="error"; quarantine="quarantine"
class ValidationOutcome(str,Enum): passed="passed"; failed="failed"; quarantined="quarantined"
@dataclass(frozen=True,slots=True)
class ValidationContext:
    rule_set_id:str; rule_set_version:int; runtime_mode:str
@dataclass(frozen=True,slots=True)
class ValidationFinding:
    code:str; severity:FindingSeverity; message:str; candidate_id:str|None=None; details:dict[str,Any]|None=None
@dataclass(frozen=True,slots=True)
class ValidationReceipt:
    validation_receipt_id:str; context:ValidationContext; outcome:ValidationOutcome; findings:tuple[ValidationFinding,...]; candidate_count:int; receipt_sha256:str
