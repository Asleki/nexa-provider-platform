"""P006.7.11.7 Bundle 17E canonical spatial persistence and governed execution."""
from .artifacts import ARTIFACT_PATHS, artifact_drift_findings, artifact_rows, write_bundle17e_artifacts
from .batch import build_spatial_preview, content_fingerprint, offline_spatial_preview
from .canonical import (
    canonical_by_candidate,
    coordinate_candidate_rows,
    derive_spatial_canonical_crosswalk,
    existing_spatial_point_mapping,
    migration_action_rows,
)
from .contracts import (
    EffectiveDatedSpatialAssignment,
    GeometryAssignmentCandidate,
    PersistenceQualificationResult,
    SpatialBatchPreview,
    SpatialCanonicalCrosswalk,
    SpatialExecutionItem,
    SpatialExecutionReceipt,
    SpatialMigrationAction,
    SpatialQualificationResult,
    TargetSpatialSnapshot,
)
from .execution import SpatialExecutionBlocked, StaleSpatialPreviewError, execute_spatial_batch
from .geometry import derive_effective_dated_assignments, derive_geometry_assignments, existing_geometry_ids, geometry_by_candidate
from .persistence import MemorySpatialRepository, PostgreSQLSpatialRepository
from .qualification import bundle17e_is_qualified, derive_persistence_qualifications, persistence_findings

__all__ = [
    "ARTIFACT_PATHS", "artifact_drift_findings", "artifact_rows", "write_bundle17e_artifacts",
    "content_fingerprint", "build_spatial_preview", "offline_spatial_preview",
    "canonical_by_candidate", "coordinate_candidate_rows", "derive_spatial_canonical_crosswalk",
    "existing_spatial_point_mapping", "migration_action_rows", "EffectiveDatedSpatialAssignment",
    "GeometryAssignmentCandidate", "PersistenceQualificationResult", "SpatialBatchPreview", "SpatialCanonicalCrosswalk",
    "SpatialExecutionItem", "SpatialExecutionReceipt", "SpatialMigrationAction", "SpatialQualificationResult",
    "TargetSpatialSnapshot", "SpatialExecutionBlocked", "StaleSpatialPreviewError", "execute_spatial_batch",
    "derive_effective_dated_assignments", "derive_geometry_assignments", "existing_geometry_ids", "geometry_by_candidate",
    "MemorySpatialRepository", "PostgreSQLSpatialRepository", "bundle17e_is_qualified",
    "derive_persistence_qualifications", "persistence_findings",
]
