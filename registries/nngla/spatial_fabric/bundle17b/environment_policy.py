"""Bundle 17B governed environmental evidence vocabulary and resolution policy."""
from __future__ import annotations

from .contracts import EnvironmentEvidenceType


def evidence_type_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        (EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION, "Value is supplied at this spatial location by qualified governed source evidence."),
        (EnvironmentEvidenceType.GOVERNED_DERIVATION, "Value is produced by a declared deterministic governed derivation from qualified evidence."),
        (EnvironmentEvidenceType.GOVERNED_INTERPOLATION, "Value is produced by a formally governed interpolation policy; reserved until such a policy exists."),
        (EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION, "No direct value exists at the point; the nearest qualified source observation is referenced without relabelling it as direct."),
        (EnvironmentEvidenceType.NOT_AVAILABLE, "No policy-authorized value is asserted at this location."),
    )
    return tuple({
        "evidence_type_code": code.value,
        "is_direct_observation": "true" if code is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "false",
        "creates_new_measured_fact": "false",
        "requires_source_reference": "true" if code is not EnvironmentEvidenceType.NOT_AVAILABLE else "false",
        "description": description,
        "status": "ACTIVE",
    } for code, description in definitions)


def environment_resolution_policy_rows() -> tuple[dict[str, str], ...]:
    rows = (
        ("ELEVATION_M", "metre", "DIRECT_SOURCE_OBSERVATION", "", False, False, False, "terrain elevation v001 supplies all 1,104 reference points"),
        ("TERRAIN_CLASS", "controlled_code", "DIRECT_SOURCE_OBSERVATION", "", False, False, False, "terrain elevation v001 supplies all 1,104 reference points"),
        ("ANNUAL_RAINFALL_MM", "millimetre_per_year", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct climate observations; nearest qualified fallback preserves evidence class"),
        ("MEAN_TEMPERATURE_C", "degree_celsius", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct climate observations; nearest qualified fallback preserves evidence class"),
        ("MEAN_WIND_SPEED_MPS", "metre_per_second", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct climate observations; nearest qualified fallback preserves evidence class"),
        ("PREVAILING_WIND_DIRECTION_DEG", "degree_clockwise_from_north", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct climate observations; nearest qualified fallback preserves evidence class"),
        ("CLIMATE_CLASS", "controlled_code", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct climate observations; nearest qualified fallback preserves evidence class"),
        ("VEGETATION_CLASS", "controlled_code", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct vegetation observations; nearest qualified fallback preserves evidence class"),
        ("ARIDITY_CLASS", "controlled_code", "DIRECT_SOURCE_OBSERVATION", "NEAREST_QUALIFIED_OBSERVATION", False, True, False, "276 direct vegetation observations; nearest qualified fallback preserves evidence class"),
        ("RAINFALL_SYSTEM_CONTEXT", "reference_identity", "GOVERNED_DERIVATION", "NOT_AVAILABLE", False, False, True, "rainfall systems remain anonymous governed systems; Bundle 17B does not invent authoritative cell membership"),
        ("HYDROLOGY_CONTEXT", "reference_identity", "DIRECT_SOURCE_OBSERVATION", "NOT_AVAILABLE", False, False, True, "only exact qualified hydrology coordinate relationships are bound here; nearest-feature query is deferred to Bundle 17O"),
    )
    out = []
    for index, (dimension, unit, preferred, fallback, interpolation, nearest, missing, basis) in enumerate(rows, start=1):
        out.append({
            "environment_policy_id": f"NG-ENV-POL-{index:04d}",
            "environment_dimension": dimension,
            "unit": unit,
            "preferred_evidence_type": preferred,
            "allowed_fallback_evidence_types": fallback,
            "source_dataset_id": {
                "ELEVATION_M": "dataset:novegeo:terrain:elevation",
                "TERRAIN_CLASS": "dataset:novegeo:terrain:elevation",
                "ANNUAL_RAINFALL_MM": "dataset:novegeo:climate:baseline",
                "MEAN_TEMPERATURE_C": "dataset:novegeo:climate:baseline",
                "MEAN_WIND_SPEED_MPS": "dataset:novegeo:climate:baseline",
                "PREVAILING_WIND_DIRECTION_DEG": "dataset:novegeo:climate:baseline",
                "CLIMATE_CLASS": "dataset:novegeo:climate:baseline",
                "VEGETATION_CLASS": "dataset:novegeo:vegetation:baseline",
                "ARIDITY_CLASS": "dataset:novegeo:vegetation:baseline",
                "RAINFALL_SYSTEM_CONTEXT": "dataset:novegeo:climate:baseline",
                "HYDROLOGY_CONTEXT": "dataset:novegeo:hydrology:surface-water",
            }[dimension],
            "resolution_basis": basis,
            "maximum_resolution_distance": "",
            "distance_unit": "decimal_degree",
            "allow_interpolation": str(interpolation).lower(),
            "allow_nearest": str(nearest).lower(),
            "allow_missing": str(missing).lower(),
            "runtime_effect_scope": "SHARED_REFERENCE",
            "status": "ACTIVE",
        })
    return tuple(out)


__all__ = ["evidence_type_rows", "environment_resolution_policy_rows"]
