"""P006.7.8 governed tenure and title-type vocabulary contracts."""
from dataclasses import dataclass

_ALLOWED_TRI={'true','false','limited'}

@dataclass(frozen=True,slots=True)
class TenureTypeDefinition:
    tenure_type_code:str
    canonical_label:str
    ownership_model:str
    transferable:str
    lease_based:bool
    state_interest_possible:bool
    status:str
    description:str
    def __post_init__(self) -> None:
        if not self.tenure_type_code or not self.canonical_label: raise ValueError("tenure identity/label required")
        if self.transferable not in _ALLOWED_TRI: raise ValueError("transferable must preserve governed true/false/limited semantics")
        if self.status!='ACTIVE': raise ValueError("Bundle 15C accepts active governed tenure types")

@dataclass(frozen=True,slots=True)
class TitleTypeDefinition:
    title_type_code:str
    canonical_label:str
    tenure_type_code:str
    registrable:bool
    transferable:str
    requires_parcel:bool
    status:str
    description:str
    def __post_init__(self) -> None:
        if not self.title_type_code or not self.tenure_type_code: raise ValueError("title type and tenure type required")
        if self.transferable not in _ALLOWED_TRI: raise ValueError("transferable must preserve governed true/false/limited semantics")
        if self.status!='ACTIVE': raise ValueError("Bundle 15C accepts active governed title types")
        if not self.requires_parcel: raise ValueError("Day-Zero title types require a parcel")

__all__=["TenureTypeDefinition","TitleTypeDefinition"]
