from decimal import Decimal
import pytest

from registries.nngla.spatial_fabric.bundle17b.contracts import (
    CrsCrosswalkEntry,
    EnvironmentEvidenceType,
    PrecisionQualification,
)
from registries.nngla.spatial_fabric.bundle17b.environment_policy import (
    environment_resolution_policy_rows,
    evidence_type_rows,
)


def test_environment_evidence_vocabulary_is_explicit_and_does_not_promote_derived_values_to_direct():
    assert [row["evidence_type_code"] for row in evidence_type_rows()] == [
        "DIRECT_SOURCE_OBSERVATION",
        "GOVERNED_DERIVATION",
        "GOVERNED_INTERPOLATION",
        "NEAREST_QUALIFIED_OBSERVATION",
        "NOT_AVAILABLE",
    ]
    assert all(row["creates_new_measured_fact"] == "false" for row in evidence_type_rows())


def test_environment_policy_reserves_interpolation_but_does_not_enable_it_without_a_governed_formula():
    policies = environment_resolution_policy_rows()
    assert len(policies) == 11
    assert all(row["allow_interpolation"] == "false" for row in policies)
    climate = next(row for row in policies if row["environment_dimension"] == "ANNUAL_RAINFALL_MM")
    assert climate["preferred_evidence_type"] == "DIRECT_SOURCE_OBSERVATION"
    assert climate["allowed_fallback_evidence_types"] == "NEAREST_QUALIFIED_OBSERVATION"
    assert climate["allow_nearest"] == "true"


def test_precision_contract_forbids_human_display_value_from_becoming_authoritative():
    with pytest.raises(ValueError):
        PrecisionQualification(
            "NG-PREC-00000001",
            "coordocc:nngla:" + "a" * 64,
            "coordcand:nngla:" + "b" * 64,
            "LONGITUDE",
            "43.753431878",
            "43.753431878",
            "43.753432",
            9,
            9,
            6,
            True,
            True,
            "PASS",
        )


def test_crs_crosswalk_contract_cannot_redirect_bundle17b_to_a_competing_crs():
    with pytest.raises(ValueError):
        CrsCrosswalkEntry(
            "NG-CRSXW-000001", "NG-SPFILE-001", "dataset:test", "EPSG:4326",
            "EPSG", "4326", "crs:novegeo:geographic", "NG-CRS-OTHER",
            "LONGITUDE_LATITUDE", "decimal_degree", "TEST", "evidence", "PASS",
        )
