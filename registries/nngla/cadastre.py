"""P006.7.7 cadastral geometry and governed land-use reference contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import re

@dataclass(frozen=True,slots=True)
class LandUseDefinition:
    land_use_code:str
    canonical_label:str
    category:str
    allows_mixed_use:bool
    legal_classification:bool
    status:str
    description:str
    def __post_init__(self) -> None:
        if not self.land_use_code or not self.canonical_label: raise ValueError("land use identity/label required")
        if self.status!='ACTIVE': raise ValueError("Bundle 15C accepts active governed land-use definitions")
        if not self.legal_classification: raise ValueError("Day-Zero NNGLA land-use codes are legal classifications")

@dataclass(frozen=True,slots=True)
class CadastralGeometryAssociation:
    parcel_id:str
    geometry_id:str
    survey_id:str | None
    geometry_role_code:str
    effective_from:date
    effective_to:date | None
    source_reference:str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NV-\d{2}-\d{3}-\d{4,}",self.parcel_id): raise ValueError("parcel_id invalid")
        if not re.fullmatch(r"NG-GEO-\d{6}",self.geometry_id): raise ValueError("geometry_id invalid")
        if self.survey_id is not None and not re.fullmatch(r"NG-SRV-\d{6}",self.survey_id): raise ValueError("survey_id invalid")
        if self.geometry_role_code not in {'CADASTRAL_BOUNDARY','PARCEL_BOUNDARY'}: raise ValueError("unsupported cadastral geometry role")
        if self.effective_to is not None and self.effective_to < self.effective_from: raise ValueError("effective_to cannot precede effective_from")
        if not self.source_reference: raise ValueError("source_reference required")

__all__=["LandUseDefinition","CadastralGeometryAssociation"]
