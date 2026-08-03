"""Strict production name-context policy."""
from .contracts import NameProductionContextRequest
class ProductionNameContextPolicy:
    def validate(self,r:NameProductionContextRequest):
        if r.runtime_mode not in {"production","simulation"}: raise ValueError("unsupported runtime_mode.")
        if r.name_kind not in {"first_name","middle_name","surname"}: raise ValueError("unsupported name_kind.")
        if r.name_kind in {"first_name","middle_name"}:
            if r.tribe_reference_id or r.origin_reference_id: raise ValueError("first and middle names cannot be tribe/origin bound in this milestone.")
        if r.name_kind=="surname":
            if r.classification=="native":
                if not r.tribe_reference_id: raise ValueError("native surname requires a tribe reference.")
                if r.origin_reference_id: raise ValueError("native surname cannot carry a foreign origin reference.")
            elif r.classification=="foreign":
                if not r.origin_reference_id or not r.language_reference_id: raise ValueError("foreign surname requires origin and language references.")
                if r.tribe_reference_id: raise ValueError("foreign surname cannot carry a NoveGeo tribe reference.")
            else: raise ValueError("surname classification must be native or foreign.")
        return r
__all__=["ProductionNameContextPolicy"]
