"""Canonical-name sex-usage classification for M009.10.1."""
from __future__ import annotations
from enum import Enum
class NameSexUsage(str, Enum):
    MALE="male"; FEMALE="female"; UNISEX="unisex"; UNSPECIFIED="unspecified"
    @classmethod
    def parse(cls,value:object)->"NameSexUsage":
        if isinstance(value,cls): return value
        if not isinstance(value,str): raise TypeError("name_sex_usage must be text or NameSexUsage.")
        try: return cls(value.strip().lower())
        except ValueError as exc: raise ValueError(f"unsupported name_sex_usage: {value!r}.") from exc
__all__=["NameSexUsage"]
