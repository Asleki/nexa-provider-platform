"""Bundle 13A source and governed-boundary qualification."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import SovereignBoundaryAssociation
from .source import CountrySourceRecord, read_country_profile


@dataclass(frozen=True, slots=True)
class Bundle13AQualificationReceipt:
    status: str
    country: CountrySourceRecord
    boundary: SovereignBoundaryAssociation
    source_sha256: str
    findings: tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualify_bundle13a_source(repository_root: str | Path) -> Bundle13AQualificationReceipt:
    root = Path(repository_root)
    profile_path = root / "data/novegeo/country/source/novegeo_country_profile.csv"
    qualification_path = root / "data/novegeo/geography/world-boundary/qualification/novegeo_world_boundary_v002_qualification.json"
    if not profile_path.is_file():
        raise FileNotFoundError(profile_path)
    if not qualification_path.is_file():
        raise FileNotFoundError(qualification_path)

    country = read_country_profile(profile_path)
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))

    if qualification.get("decision") != "qualified":
        raise ValueError("sovereign boundary must already be qualified by the locked geography authority.")
    if qualification.get("boundaryId") != "boundary:novegeo:sovereign":
        raise ValueError("unexpected sovereign boundary identity.")
    if int(qualification.get("boundaryVersion", 0)) != country.active_boundary_version:
        raise ValueError("country active boundary version does not match governed geography qualification.")
    if qualification.get("runtimeMode") != "shared_reference":
        raise ValueError("country must reference shared_reference sovereign geography.")
    if qualification.get("coordinateReferenceId") != "crs:novegeo:geographic":
        raise ValueError("country sovereign boundary must preserve the governed NoveGeo CRS identity.")
    if int(qualification.get("mainlandVertexCount", 0)) <= 0:
        raise ValueError("qualified sovereign boundary must preserve a mainland geometry.")
    if int(qualification.get("offshoreIslandCount", -1)) != 5:
        raise ValueError("qualified NoveGeo boundary must preserve five offshore islands.")

    boundary = SovereignBoundaryAssociation(
        association_id=f"country-boundary:novegeo:v{country.active_boundary_version:03d}",
        country_id=country.identity.country_id,
        boundary_id=qualification["boundaryId"],
        boundary_version=int(qualification["boundaryVersion"]),
        coordinate_reference_id=qualification["coordinateReferenceId"],
        coordinate_reference_version=int(qualification["coordinateReferenceVersion"]),
        runtime_mode=qualification["runtimeMode"],
        qualification_id=qualification["qualificationId"],
    )
    findings = (
        "COUNTRY_IDENTITY_VALID",
        "SYNTHETIC_ALPHA2_VALID",
        "SYNTHETIC_ALPHA3_VALID",
        "EXTERNAL_ISO_CLAIM_ABSENT",
        "GOVERNED_BOUNDARY_ID_CONTINUITY",
        "GOVERNED_BOUNDARY_VERSION_MATCH",
        "SHARED_REFERENCE_GEOGRAPHY_PRESERVED",
        "CRS_CONTINUITY_PRESERVED",
        "MAINLAND_AND_ISLANDS_PRESERVED",
        "CSV_RUNTIME_AUTHORITY_PROHIBITED",
    )
    return Bundle13AQualificationReceipt(
        status="PASSED",
        country=country,
        boundary=boundary,
        source_sha256=_sha256(profile_path),
        findings=findings,
    )
