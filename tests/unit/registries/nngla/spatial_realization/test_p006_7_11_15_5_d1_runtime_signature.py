from registries.nngla.spatial_realization.runtime_signature import (
    DEFAULT_PRECISION_POLICY_ID,
    DIAGNOSTIC_CRS,
    ENGINE_FAMILY,
    TOPOLOGY_CRS,
    detect_runtime_signature,
)


def test_delivery1_runtime_signature_binds_geometry_projection_and_precision_versions():
    signature = detect_runtime_signature()
    assert signature.engine_family == ENGINE_FAMILY
    assert signature.topology_crs == TOPOLOGY_CRS == "EPSG:4326"
    assert signature.diagnostic_crs == DIAGNOSTIC_CRS == "EPSG:6933"
    assert signature.precision_policy_id == DEFAULT_PRECISION_POLICY_ID
    assert signature.geometry_engine_version
    assert signature.geos_version
    assert signature.projection_engine_version
    assert signature.proj_version
    assert len(signature.digest) == 64


def test_delivery1_runtime_signature_is_repeatable_with_same_runtime():
    assert detect_runtime_signature().digest == detect_runtime_signature().digest
