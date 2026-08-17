"""Bundle 17I sovereign title-number series policy."""
from __future__ import annotations
from .contracts import TitleNumberSeriesDefinition


def title_number_series_rows() -> tuple[dict[str, str], ...]:
    return ({
        "series_id": "titleseries:nngla:sovereign",
        "title_id_pattern": r"^NG-TTL-\d{6}$",
        "allocation_scope": "SOVEREIGN_GLOBAL",
        "prefix": "NG-TTL-",
        "sequence_width": "6",
        "minimum_sequence": "1",
        "sequence_semantics": "MONOTONIC_NO_REUSE",
        "issuing_authority_code": "NNGLA",
        "reservation_runtime": "PRODUCTION_AUTHORITY",
        "status": "ACTIVE",
        "description": "Sovereign title-number reference series; reservation does not constitute title issuance.",
    },)


def load_title_series() -> TitleNumberSeriesDefinition:
    row = title_number_series_rows()[0]
    return TitleNumberSeriesDefinition(
        series_id=row["series_id"], title_id_pattern=row["title_id_pattern"], allocation_scope=row["allocation_scope"],
        prefix=row["prefix"], sequence_width=int(row["sequence_width"]), minimum_sequence=int(row["minimum_sequence"]),
        sequence_semantics=row["sequence_semantics"], issuing_authority_code=row["issuing_authority_code"],
        reservation_runtime=row["reservation_runtime"], status=row["status"],
    )


__all__ = ["title_number_series_rows", "load_title_series"]
