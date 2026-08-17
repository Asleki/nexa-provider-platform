"""Bundle 17F reconciliation of locked canonical objects without regeneration."""
from __future__ import annotations
from functools import lru_cache

from ._shared import (
    ADMIN_PATH, FEATURE_PATH, GEOMETRY_PATH, LOCKED_CANONICAL_COUNTS, PLACE_PATH, ROAD_PATH, ROOT,
    csv_rows, file_sha256, governed_suffix,
)
from .contracts import CanonicalSubjectFamily, ExistingCanonicalAlignment


def _row(
    *, family: CanonicalSubjectFamily, source_record_id: str, candidate_id: str, canonical_id: str,
    ordinal: int, source_path, identity_status: str, geometry_status: str = "NO_ASSOCIABLE_GEOMETRY_SOURCE",
    geometry_id: str = "", database_status: str = "LOCKED_BASELINE_ASSERTED_REQUIRES_LIVE_RECHECK", notes: str = "",
) -> ExistingCanonicalAlignment:
    return ExistingCanonicalAlignment(
        alignment_id=f"align:nngla:{family.value.lower()}:{canonical_id}",
        object_family=family,
        source_record_id=source_record_id,
        candidate_id=candidate_id,
        canonical_id=canonical_id,
        canonical_ordinal=ordinal,
        source_path=str(source_path.relative_to(ROOT)),
        source_sha256=file_sha256(source_path),
        identity_status=identity_status,
        geometry_status=geometry_status,
        geometry_id=geometry_id,
        database_verification_status=database_status,
        runtime_effect_scope="SHARED_REFERENCE",
        notes=notes,
    )


@lru_cache(maxsize=1)
def derive_existing_canonical_alignment() -> tuple[ExistingCanonicalAlignment, ...]:
    out: list[ExistingCanonicalAlignment] = []

    for ordinal, row in enumerate(csv_rows(PLACE_PATH), start=1):
        suffix = governed_suffix(row["source_place_code"])
        out.append(_row(
            family=CanonicalSubjectFamily.PLACE,
            source_record_id=row["source_place_code"], candidate_id=row["settlement_name_record_id"],
            canonical_id=f"NG-PLC-{suffix}", ordinal=ordinal, source_path=PLACE_PATH,
            identity_status="CANONICAL_IDENTITY_PRESERVED_FROM_LOCKED_SUFFIX_ALLOCATION",
            notes="Spatial association remains deferred until governed settlement geometry exists.",
        ))

    for ordinal, row in enumerate(csv_rows(ADMIN_PATH), start=1):
        suffix = governed_suffix(row["administrative_candidate_id"])
        out.append(_row(
            family=CanonicalSubjectFamily.ADMINISTRATIVE_AREA,
            source_record_id=row["source_record_id"], candidate_id=row["administrative_candidate_id"],
            canonical_id=f"NG-ADM-{suffix}", ordinal=ordinal, source_path=ADMIN_PATH,
            identity_status="CANONICAL_IDENTITY_PRESERVED_FROM_LOCKED_SUFFIX_ALLOCATION",
            notes="Boundary geometry remains deferred; no polygon is fabricated from hierarchy alone.",
        ))

    roads = csv_rows(ROAD_PATH)
    for ordinal, row in enumerate(roads[:LOCKED_CANONICAL_COUNTS["ROAD"]], start=1):
        suffix = governed_suffix(row["road_candidate_id"])
        out.append(_row(
            family=CanonicalSubjectFamily.ROAD,
            source_record_id=row["road_candidate_id"], candidate_id=row["road_candidate_id"],
            canonical_id=f"NG-RD-{suffix}", ordinal=ordinal, source_path=ROAD_PATH,
            identity_status="CANONICAL_IDENTITY_PRESERVED_FROM_LOCKED_FIRST_350_ROAD_BASELINE",
            notes="Only the first 350 road source candidates are aligned to the locked canonical road baseline.",
        ))

    geometries = csv_rows(GEOMETRY_PATH)
    geometry_by_subject = {row["subject_id"]: row for row in geometries}
    for ordinal, row in enumerate(csv_rows(FEATURE_PATH), start=1):
        match = geometry_by_subject.get(row["source_feature_id"])
        if match is not None:
            geometry_status = "DIRECT_EXISTING_GEOMETRY_SUBJECT_MATCH"
            geometry_id = match["geometry_version_candidate_id"]
            notes = "Existing feature source subject directly matches existing geometry subject."
        elif row["feature_type_code"] == "MAINLAND" and row["source_feature_id"] == "boundary-part:1":
            geometry_status = "RELATED_SOVEREIGN_GEOMETRY_NOT_DIRECT_SUBJECT_MATCH"
            geometry_id = "NG-GEO-000001"
            notes = "MAINLAND feature is not silently equated with COUNTRY sovereign-boundary subject."
        else:
            geometry_status = "NO_ASSOCIABLE_GEOMETRY_SOURCE"
            geometry_id = ""
            notes = "No existing governed geometry subject match."
        out.append(_row(
            family=CanonicalSubjectFamily.GEOGRAPHIC_FEATURE,
            source_record_id=row["source_feature_id"], candidate_id=row["feature_candidate_id"],
            canonical_id=row["feature_candidate_id"], ordinal=ordinal, source_path=FEATURE_PATH,
            identity_status="EXISTING_CANONICAL_FEATURE_IDENTITY_PRESERVED",
            geometry_status=geometry_status, geometry_id=geometry_id, notes=notes,
        ))

    for ordinal, row in enumerate(geometries, start=1):
        out.append(_row(
            family=CanonicalSubjectFamily.EXISTING_GEOMETRY,
            source_record_id=row["source_geometry_id"], candidate_id=row["geometry_version_candidate_id"],
            canonical_id=row["geometry_version_candidate_id"], ordinal=ordinal, source_path=GEOMETRY_PATH,
            identity_status="EXISTING_GEOMETRY_IDENTITY_PRESERVED",
            geometry_status="EXISTING_GEOMETRY_RECORD_PRESERVED", geometry_id=row["geometry_version_candidate_id"],
            database_status="SOURCE_GEOMETRY_RECORD_NO_SEPARATE_OBJECT_RECHECK",
            notes="Existing geometry allocations remain immutable; Bundle 17F creates no replacement geometry IDs.",
        ))

    expected = sum(LOCKED_CANONICAL_COUNTS.values())
    if len(out) != expected:
        raise ValueError(f"locked canonical alignment count drift: expected {expected}, got {len(out)}")
    if len({row.canonical_id for row in out if row.object_family is not CanonicalSubjectFamily.EXISTING_GEOMETRY}) != 1263:
        raise ValueError("canonical subject identity collision in Bundle 17F alignment")
    return tuple(out)


def remaining_noncanonical_road_candidate_ids() -> tuple[str, ...]:
    rows = csv_rows(ROAD_PATH)
    return tuple(row["road_candidate_id"] for row in rows[LOCKED_CANONICAL_COUNTS["ROAD"]:])


def alignment_counts() -> dict[str, int]:
    counts = {key: 0 for key in LOCKED_CANONICAL_COUNTS}
    for row in derive_existing_canonical_alignment():
        counts[row.object_family.value] += 1
    return counts


__all__ = ["derive_existing_canonical_alignment", "remaining_noncanonical_road_candidate_ids", "alignment_counts"]
