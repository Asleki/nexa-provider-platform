"""Bundle 17B precision qualification preserving source/canonical/display separation."""
from __future__ import annotations

from functools import lru_cache
from decimal import Decimal, ROUND_HALF_EVEN

from registries.nngla.spatial_fabric import candidate_identity, derive_coordinate_occurrences
from registries.nngla.spatial_fabric.contracts import canonical_decimal_text

from ._shared import decimal_places
from .contracts import PrecisionQualification
from .crs_reconciliation import crs_by_source_file


_DISPLAY_QUANTUM = Decimal("0.000001")


def _display_text(value: Decimal) -> str:
    canonical = canonical_decimal_text(value)
    if decimal_places(canonical) <= 6:
        return canonical
    rounded = value.quantize(_DISPLAY_QUANTUM, rounding=ROUND_HALF_EVEN)
    return canonical_decimal_text(rounded)


@lru_cache(maxsize=1)
def derive_precision_qualifications() -> tuple[PrecisionQualification, ...]:
    crs = crs_by_source_file()
    out: list[PrecisionQualification] = []
    sequence = 0
    for occurrence in derive_coordinate_occurrences():
        if occurrence.source_file_id not in crs:
            raise ValueError(f"CRS unresolved for {occurrence.coordinate_occurrence_id}")
        candidate_id = candidate_identity(occurrence.source_longitude_numeric, occurrence.source_latitude_numeric)
        axes = (
            ("LONGITUDE", occurrence.source_longitude_text, occurrence.source_longitude_numeric),
            ("LATITUDE", occurrence.source_latitude_text, occurrence.source_latitude_numeric),
        )
        for axis, source_text, numeric in axes:
            sequence += 1
            canonical = canonical_decimal_text(numeric)
            display = _display_text(numeric)
            out.append(PrecisionQualification(
                precision_qualification_id=f"NG-PREC-{sequence:08d}",
                coordinate_occurrence_id=occurrence.coordinate_occurrence_id,
                coordinate_candidate_id=candidate_id,
                axis=axis,
                source_value=source_text,
                canonical_value=canonical,
                display_value=display,
                source_decimal_places=decimal_places(source_text),
                canonical_decimal_places=decimal_places(canonical),
                display_decimal_places=decimal_places(display),
                round_trip_same_location=Decimal(source_text) == Decimal(canonical),
                display_is_authoritative=False,
                precision_status="PASS",
            ))
    return tuple(out)


def precision_findings(rows: tuple[PrecisionQualification, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_precision_qualifications()
    findings: list[str] = []
    for row in current:
        if row.display_is_authoritative:
            findings.append(f"DISPLAY_BECAME_AUTHORITATIVE:{row.precision_qualification_id}")
        if not row.round_trip_same_location:
            findings.append(f"CANONICAL_LOCATION_MOVED:{row.precision_qualification_id}")
        if row.precision_status != "PASS":
            findings.append(f"PRECISION_FAILED:{row.precision_qualification_id}")
    return tuple(findings)


__all__ = ["derive_precision_qualifications", "precision_findings"]
