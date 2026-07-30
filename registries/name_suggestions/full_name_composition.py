"""Supported M009.2.5 full-name composition shapes."""
from enum import Enum

class FullNameComposition(str,Enum):
    SINGLE_FIRST="single_first"
    FIRST_SURNAME="first_surname"
    FIRST_MIDDLE_SURNAME="first_middle_surname"
    @classmethod
    def parse(cls,value:object)->"FullNameComposition":
        if isinstance(value,cls): return value
        if not isinstance(value,str): raise TypeError("composition must be text or FullNameComposition.")
        try: return cls(value.strip().lower())
        except ValueError as exc: raise ValueError(f"unsupported full-name composition: {value!r}.") from exc

__all__=["FullNameComposition"]
