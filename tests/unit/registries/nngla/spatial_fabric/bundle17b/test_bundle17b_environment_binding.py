from collections import Counter

from registries.nngla.spatial_fabric.bundle17b.contracts import EnvironmentEvidenceType
from registries.nngla.spatial_fabric.bundle17b.environment_binding import (
    derive_environment_bindings,
    environment_binding_findings,
    environment_coverage_rows,
)


def test_1104_reference_ground_points_receive_environment_bindings_without_fabricating_direct_climate():
    rows = derive_environment_bindings()
    assert len(rows) == 1104
    assert environment_binding_findings(rows) == ()
    assert Counter(row.climate_evidence_type for row in rows) == Counter({
        EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION: 828,
        EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION: 276,
    })
    assert Counter(row.vegetation_evidence_type for row in rows) == Counter({
        EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION: 828,
        EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION: 276,
    })


def test_elevation_and_terrain_remain_1104_direct_source_observations_and_interpolation_is_unused():
    rows = derive_environment_bindings()
    assert all(row.elevation_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION for row in rows)
    assert all(row.terrain_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION for row in rows)
    used = {row.climate_evidence_type for row in rows} | {row.vegetation_evidence_type for row in rows}
    assert EnvironmentEvidenceType.GOVERNED_INTERPOLATION not in used


def test_nearest_climate_and_vegetation_values_keep_the_source_observation_identity_and_distance():
    rows = {row.spatial_point_id: row for row in derive_environment_bindings()}
    point = rows["NG-SPT-000002"]
    assert point.climate_observation_id == "NG-CLIM-OBS-000001"
    assert point.climate_evidence_type is EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION
    assert point.climate_resolution_distance_degrees == "0.42"
    assert point.vegetation_observation_id == "NG-VEG-OBS-000001"
    assert point.vegetation_evidence_type is EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION


def test_hydrology_is_bound_only_where_exact_qualified_evidence_exists_and_absence_is_not_inferred():
    rows = derive_environment_bindings()
    assert Counter(row.hydrology_evidence_type for row in rows) == Counter({
        EnvironmentEvidenceType.NOT_AVAILABLE: 1092,
        EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION: 12,
    })
    coverage = environment_coverage_rows(rows)
    assert len(coverage) == 1104
    assert all(row["overall_coverage_status"] == "PASS" for row in coverage)
