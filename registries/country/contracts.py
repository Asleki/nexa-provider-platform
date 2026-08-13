"""P006.7.1 Bundle 13A sovereign-country reference contracts.

These contracts establish NoveGeo's stable sovereign identity, synthetic
country-code assignments, and a reference to the already-governed sovereign
boundary. They do not own geography, runtime policy, currency authority,
locale policy, citizens, parcels, or any later registry domain.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

_COUNTRY_ID = re.compile(r"^country:[a-z][a-z0-9_-]{1,63}$")
_BOUNDARY_ID = re.compile(r"^boundary:[a-z0-9][a-z0-9:_-]{1,127}$")
_CRS_ID = re.compile(r"^crs:[a-z0-9][a-z0-9:_-]{1,127}$")


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return " ".join(value.strip().split())


class SovereigntyStatus(str, Enum):
    SIMULATED_SOVEREIGN = "SIMULATED_SOVEREIGN"


class CountryLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUPERSEDED = "SUPERSEDED"


class CountryCodeKind(str, Enum):
    ALPHA2 = "ALPHA2"
    ALPHA3 = "ALPHA3"


class CountryCodeScheme(str, Enum):
    """Internal sovereign scheme; deliberately not an ISO assignment claim."""

    NOVEGEO_SOVEREIGN = "NOVEGEO_SOVEREIGN"


@dataclass(frozen=True, slots=True)
class CountryIdentity:
    country_id: str
    official_name: str
    short_name: str
    sovereignty_status: SovereigntyStatus | str
    status: CountryLifecycleStatus | str
    effective_from: date
    effective_to: date | None = None
    record_version: int = 1
    source_reference: str = ""

    def __post_init__(self) -> None:
        country_id = _required_text(self.country_id, "country_id").lower()
        if not _COUNTRY_ID.fullmatch(country_id):
            raise ValueError("country_id must use the country:<stable-key> namespace.")
        object.__setattr__(self, "country_id", country_id)
        object.__setattr__(self, "official_name", _required_text(self.official_name, "official_name"))
        object.__setattr__(self, "short_name", _required_text(self.short_name, "short_name"))
        object.__setattr__(
            self,
            "sovereignty_status",
            self.sovereignty_status
            if isinstance(self.sovereignty_status, SovereigntyStatus)
            else SovereigntyStatus(str(self.sovereignty_status).upper()),
        )
        object.__setattr__(
            self,
            "status",
            self.status
            if isinstance(self.status, CountryLifecycleStatus)
            else CountryLifecycleStatus(str(self.status).upper()),
        )
        if not isinstance(self.effective_from, date):
            raise TypeError("effective_from must be a date.")
        if self.effective_to is not None:
            if not isinstance(self.effective_to, date):
                raise TypeError("effective_to must be a date or None.")
            if self.effective_to < self.effective_from:
                raise ValueError("effective_to cannot precede effective_from.")
        if isinstance(self.record_version, bool) or not isinstance(self.record_version, int) or self.record_version < 1:
            raise ValueError("record_version must be a positive integer.")
        if self.source_reference:
            object.__setattr__(self, "source_reference", _required_text(self.source_reference, "source_reference"))


@dataclass(frozen=True, slots=True)
class CountryCodeAssignment:
    country_id: str
    code_kind: CountryCodeKind | str
    code_value: str
    scheme: CountryCodeScheme | str = CountryCodeScheme.NOVEGEO_SOVEREIGN
    issuing_authority: str = "NoveGeo sovereign reference authority"
    external_iso_assignment: bool = False
    effective_from: date = date(2026, 8, 12)
    effective_to: date | None = None

    def __post_init__(self) -> None:
        country_id = _required_text(self.country_id, "country_id").lower()
        if not _COUNTRY_ID.fullmatch(country_id):
            raise ValueError("country_id must use the country:<stable-key> namespace.")
        object.__setattr__(self, "country_id", country_id)
        kind = self.code_kind if isinstance(self.code_kind, CountryCodeKind) else CountryCodeKind(str(self.code_kind).upper())
        scheme = self.scheme if isinstance(self.scheme, CountryCodeScheme) else CountryCodeScheme(str(self.scheme).upper())
        value = _required_text(self.code_value, "code_value").upper()
        expected_length = 2 if kind is CountryCodeKind.ALPHA2 else 3
        if len(value) != expected_length or not value.isalpha() or not value.isascii():
            raise ValueError(f"{kind.value} code must be exactly {expected_length} ASCII letters.")
        if self.external_iso_assignment:
            raise ValueError("NoveGeo synthetic country codes must not claim external ISO assignment.")
        object.__setattr__(self, "code_kind", kind)
        object.__setattr__(self, "scheme", scheme)
        object.__setattr__(self, "code_value", value)
        object.__setattr__(self, "issuing_authority", _required_text(self.issuing_authority, "issuing_authority"))
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from.")


@dataclass(frozen=True, slots=True)
class SovereignBoundaryAssociation:
    association_id: str
    country_id: str
    boundary_id: str
    boundary_version: int
    coordinate_reference_id: str
    coordinate_reference_version: int
    runtime_mode: str
    association_role: str = "SOVEREIGN_TERRITORY"
    qualification_id: str = ""

    def __post_init__(self) -> None:
        association_id = _required_text(self.association_id, "association_id").lower()
        country_id = _required_text(self.country_id, "country_id").lower()
        boundary_id = _required_text(self.boundary_id, "boundary_id").lower()
        crs_id = _required_text(self.coordinate_reference_id, "coordinate_reference_id").lower()
        if not association_id.startswith("country-boundary:"):
            raise ValueError("association_id must use the country-boundary: namespace.")
        if not _COUNTRY_ID.fullmatch(country_id):
            raise ValueError("country_id must use the country:<stable-key> namespace.")
        if not _BOUNDARY_ID.fullmatch(boundary_id):
            raise ValueError("boundary_id must use the boundary: namespace.")
        if not _CRS_ID.fullmatch(crs_id):
            raise ValueError("coordinate_reference_id must use the crs: namespace.")
        if self.boundary_version < 1 or self.coordinate_reference_version < 1:
            raise ValueError("boundary and coordinate-reference versions must be positive.")
        runtime_mode = _required_text(self.runtime_mode, "runtime_mode").lower()
        if runtime_mode != "shared_reference":
            raise ValueError("sovereign boundary association must preserve shared_reference geography.")
        role = _required_text(self.association_role, "association_role").upper()
        if role != "SOVEREIGN_TERRITORY":
            raise ValueError("unsupported sovereign boundary association role.")
        if self.qualification_id and not self.qualification_id.startswith("qualification:"):
            raise ValueError("qualification_id must use the qualification: namespace.")
        object.__setattr__(self, "association_id", association_id)
        object.__setattr__(self, "country_id", country_id)
        object.__setattr__(self, "boundary_id", boundary_id)
        object.__setattr__(self, "coordinate_reference_id", crs_id)
        object.__setattr__(self, "runtime_mode", runtime_mode)
        object.__setattr__(self, "association_role", role)
