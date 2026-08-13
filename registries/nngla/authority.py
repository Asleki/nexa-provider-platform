"""P006.7.2.1 NNGLA authority registry contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

_AUTHORITY_ID = re.compile(r"^authority:[a-z0-9][a-z0-9:_-]{1,127}$")

class AuthorityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUPERSEDED = "SUPERSEDED"

class AuthorityRoleCode(str, Enum):
    GEOGRAPHIC_NAMES = "GEOGRAPHIC_NAMES"
    SURVEY_GEODESY = "SURVEY_GEODESY"
    MAPPING = "MAPPING"
    ADMINISTRATIVE_GEOGRAPHY = "ADMINISTRATIVE_GEOGRAPHY"
    ROAD_ADDRESS_REFERENCE = "ROAD_ADDRESS_REFERENCE"
    PARCEL_CADASTRE = "PARCEL_CADASTRE"
    LAND_TITLE = "LAND_TITLE"
    STATE_LAND = "STATE_LAND"
    DATA_GOVERNANCE = "DATA_GOVERNANCE"
    AUDIT = "AUDIT"

@dataclass(frozen=True, slots=True)
class NNGLAAuthority:
    authority_id: str
    authority_code: str
    official_name: str
    authority_type: str
    world_realm_id: str
    country_record_id: str
    mandate_summary: str
    status: AuthorityStatus
    effective_from: date
    effective_to: date | None = None
    source_reference: str = ""

    def __post_init__(self) -> None:
        if not _AUTHORITY_ID.fullmatch(self.authority_id):
            raise ValueError("authority_id must use authority:<stable-key> namespace")
        if self.authority_code != "NNGLA":
            raise ValueError("Bundle 14A authority code must be NNGLA")
        if self.country_record_id != "country:novegeo":
            raise ValueError("NNGLA must reference country:novegeo")
        if self.world_realm_id != "realm:nexilabs:novegeo":
            raise ValueError("NNGLA must reference realm:nexilabs:novegeo")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")

@dataclass(frozen=True, slots=True)
class NNGLAAuthorityRole:
    authority_role_id: str
    authority_id: str
    role_code: AuthorityRoleCode
    role_name: str
    domain_scope: str
    may_create: bool
    may_review: bool
    may_approve: bool
    may_gazette: bool
    may_retire: bool
    status: AuthorityStatus
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        if self.authority_id != "authority:nngla":
            raise ValueError("NNGLA roles must belong to authority:nngla")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")
