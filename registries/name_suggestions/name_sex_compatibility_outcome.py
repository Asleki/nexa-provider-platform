"""Outcomes for M009.10.2 name/sex compatibility evaluation."""
from enum import Enum
class NameSexCompatibilityOutcome(str,Enum):
    COMPATIBLE="compatible"; AMBIGUOUS="ambiguous"; UNSPECIFIED="unspecified"; CONFLICT="conflict"
__all__=["NameSexCompatibilityOutcome"]
