"""Bundle 17G cadastral-series semantics independent from administrative boundaries."""
from __future__ import annotations
from .contracts import CadastralSeriesPolicy


def cadastral_series_policy_rows() -> tuple[dict[str, str], ...]:
    return ({
        "definition_id": "cadseries-policy:nngla:default",
        "parcel_id_pattern": r"^NV-\d{2}-\d{3}-\d{4,}$",
        "cadastral_zone_semantics": "GOVERNED_CADASTRAL_ZONE_NOT_ADMINISTRATIVE_AREA",
        "cadastral_series_semantics": "GOVERNED_SERIES_WITHIN_CADASTRAL_ZONE",
        "sequence_semantics": "MONOTONIC_SERIES_LOCAL_NO_REUSE",
        "minimum_sequence_width": "4",
        "allocation_authority_code": "NNGLA",
        "sovereign_reservation_runtime": "PRODUCTION_AUTHORITY",
        "administrative_area_dependency": "INDEPENDENT_OF_ADMINISTRATIVE_BOUNDARIES",
        "status": "ACTIVE",
    },)


def load_policy() -> CadastralSeriesPolicy:
    row = cadastral_series_policy_rows()[0]
    return CadastralSeriesPolicy(
        definition_id=row["definition_id"], parcel_id_pattern=row["parcel_id_pattern"],
        cadastral_zone_semantics=row["cadastral_zone_semantics"], cadastral_series_semantics=row["cadastral_series_semantics"],
        sequence_semantics=row["sequence_semantics"], minimum_sequence_width=int(row["minimum_sequence_width"]),
        allocation_authority_code=row["allocation_authority_code"], sovereign_reservation_runtime=row["sovereign_reservation_runtime"],
        administrative_area_dependency=row["administrative_area_dependency"], status=row["status"],
    )


__all__ = ["cadastral_series_policy_rows", "load_policy"]
