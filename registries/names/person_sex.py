"""Person-sex reference contract for M009.10.1."""
from __future__ import annotations
from enum import Enum
class PersonSex(str, Enum):
    MALE="male"; FEMALE="female"; INTERSEX="intersex"; UNSPECIFIED="unspecified"
    @classmethod
    def parse(cls,value:object)->"PersonSex":
        if isinstance(value,cls): return value
        if not isinstance(value,str): raise TypeError("person_sex must be text or PersonSex.")
        try: return cls(value.strip().lower())
        except ValueError as exc: raise ValueError(f"unsupported person_sex: {value!r}.") from exc
__all__=["PersonSex"]
