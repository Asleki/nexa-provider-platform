"""P006.7.11.10 — Place Spatial Association and Settlement Geometry."""
from .artifacts import ALL_BUNDLE_ARTIFACTS, CONTROLLED_ARTIFACTS, MATERIALIZED_ARTIFACTS, artifact_findings
from .execution import bundle_fingerprint, bundle_source_hashes, execute_place_spatialization
from .footprints import derive_point_only_exceptions, derive_settlement_footprints
from .handlers import make_geometry_association_handler, register_bundle19a_runtime_handlers
from .materialize import materialize_bundle19a_artifacts
from .persistence import MemoryPlaceSpatialRepository, PostgreSQLPlaceSpatialRepository
from .qualification import bundle19a_is_qualified, qualification_findings
from .relationships import derive_place_spatial_relationships
from .siting import derive_place_reference_points

__all__ = [
    "ALL_BUNDLE_ARTIFACTS", "CONTROLLED_ARTIFACTS", "MATERIALIZED_ARTIFACTS", "artifact_findings",
    "bundle_fingerprint", "bundle_source_hashes", "execute_place_spatialization",
    "derive_point_only_exceptions", "derive_settlement_footprints",
    "make_geometry_association_handler", "register_bundle19a_runtime_handlers",
    "materialize_bundle19a_artifacts", "MemoryPlaceSpatialRepository", "PostgreSQLPlaceSpatialRepository",
    "bundle19a_is_qualified", "qualification_findings", "derive_place_spatial_relationships", "derive_place_reference_points",
]
