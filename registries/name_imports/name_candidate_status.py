from enum import Enum
class NameCandidateStatus(str,Enum):
    STAGED="staged"; VALIDATED="validated"; QUARANTINED="quarantined"; REJECTED="rejected"; APPROVED="approved"; IMPORTED="imported"
    @classmethod
    def parse(cls,value:object)->"NameCandidateStatus":
        if isinstance(value,cls): return value
        if not isinstance(value,str): raise TypeError("candidate status must be text or NameCandidateStatus.")
        try:return cls(value.strip().lower())
        except ValueError as exc: raise ValueError(f"unsupported candidate status: {value!r}.") from exc
__all__=["NameCandidateStatus"]
