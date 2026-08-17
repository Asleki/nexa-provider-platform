"""Scope-aware, ambiguity-preserving geographic-name geocoding."""
from __future__ import annotations
from ._shared import GEOCODING_RULES_PATH,csv_rows,normalize_name_text
from .contracts import GeocodeMatch,GeocodeResult,GeocodeStatus

def geocoding_rules(): return csv_rows(GEOCODING_RULES_PATH)
class MemoryGeocoder:
    def __init__(self,matches=()): self.matches=tuple(matches)
    def geocode(self,text: str,*,scope_reference: str|None=None,runtime_mode: str|None=None,allow_restricted=False,limit=100):
        normalized=normalize_name_text(text)
        visible=[]; restricted=False
        for m in self.matches:
            if runtime_mode is not None and m.runtime_mode!=runtime_mode: continue
            if normalize_name_text(m.display_name)!=normalized: continue
            if scope_reference is not None and m.scope_reference!=scope_reference: continue
            if m.visibility!="PUBLIC" and not allow_restricted:
                restricted=True; continue
            visible.append(m)
        visible=tuple(visible[:limit])
        if len(visible)==1: status=GeocodeStatus.UNIQUE_MATCH
        elif len(visible)>1: status=GeocodeStatus.MULTIPLE_MATCHES
        elif restricted: status=GeocodeStatus.RESTRICTED_MATCH_EXISTS
        else: status=GeocodeStatus.NO_MATCH
        return GeocodeResult(status,normalized,visible)
__all__=["geocoding_rules","MemoryGeocoder"]
