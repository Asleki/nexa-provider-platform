"""Governed NoveGeo world geometry authority for P004.1-P004.2."""
from .contracts import (
    BoundaryIdentity,
    CoordinateReference,
    GeographicCoordinate,
    ProjectedCoordinate,
    WorldBoundaryCandidate,
    WorldBoundaryPublication,
)
from .geometry import BoundaryValidationError, normalize_boundary_geometry, validate_boundary_geometry
from .projection import EquirectangularWorldProjection
from .qualification import WorldBoundaryQualificationService
from .repository import InMemoryWorldBoundaryRepository, WorldBoundaryRepository
from .service import WorldGeometryService, build_default_world_geometry_service

__all__ = [
    "BoundaryIdentity",
    "BoundaryValidationError",
    "CoordinateReference",
    "EquirectangularWorldProjection",
    "GeographicCoordinate",
    "InMemoryWorldBoundaryRepository",
    "ProjectedCoordinate",
    "WorldBoundaryCandidate",
    "WorldBoundaryPublication",
    "WorldBoundaryQualificationService",
    "WorldBoundaryRepository",
    "WorldGeometryService",
    "build_default_world_geometry_service",
    "normalize_boundary_geometry",
    "validate_boundary_geometry",
]
