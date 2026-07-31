"""Immutable transport row produced by the local name CSV adapter."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

@dataclass(frozen=True, slots=True)
class NameCsvRow:
    row_number: int
    values: Mapping[str, str]
    def __post_init__(self)->None:
        if isinstance(self.row_number,bool) or not isinstance(self.row_number,int): raise TypeError("row_number must be an integer.")
        if self.row_number < 2: raise ValueError("row_number must be at least 2 because row 1 is the header.")
        if not isinstance(self.values,Mapping): raise TypeError("values must be a mapping.")
        normalized={}
        for raw_key,raw_value in self.values.items():
            if not isinstance(raw_key,str) or not isinstance(raw_value,str): raise TypeError("CSV row keys and values must be text.")
            key=raw_key.strip().lower()
            if not key: raise ValueError("CSV row keys cannot be empty.")
            if key in normalized: raise ValueError("CSV row keys must remain unique after normalization.")
            normalized[key]=raw_value.strip()
        object.__setattr__(self,"values",MappingProxyType(normalized))
    def get(self,key:str,default:str="")->str:
        if not isinstance(key,str): raise TypeError("key must be text.")
        return self.values.get(key.strip().lower(),default)
__all__=["NameCsvRow"]
