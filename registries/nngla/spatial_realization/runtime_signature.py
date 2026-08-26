"""Runtime fingerprinting for the P006.7.11.15.5 Delivery-1 read-only fabric prototype.

The signature is evidence, not an authorization token.  It binds geometry-engine,
projection-engine, CRS and precision-policy versions so a face/edge manifest can
be replayed and compared without implying that the prototype may write canonical
NNGLA state.
"""
from __future__ import annotations

import platform

from .contracts import FabricRuntimeSignature

TOPOLOGY_CRS = "EPSG:4326"
DIAGNOSTIC_CRS = "EPSG:6933"
DEFAULT_PRECISION_POLICY_ID = "SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP"
TEST_PRECISION_POLICY_ID = "TEST_ONLY_EXPLICIT_PRECISION_FIXTURE"
ENGINE_FAMILY = "SHAPELY_READ_ONLY_PROTOTYPE"


def detect_runtime_signature(*, precision_policy_id: str = DEFAULT_PRECISION_POLICY_ID, precision_grid: float | None = None) -> FabricRuntimeSignature:
    try:
        import shapely
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("shapely is required for Delivery-1 shared-face verification") from exc
    try:
        import pyproj
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("pyproj is required for Delivery-1 shared-face verification") from exc

    return FabricRuntimeSignature(
        engine_family=ENGINE_FAMILY,
        python_version=platform.python_version(),
        geometry_engine_version=str(shapely.__version__),
        geos_version=str(shapely.geos_version_string),
        projection_engine_version=str(pyproj.__version__),
        proj_version=str(pyproj.proj_version_str),
        topology_crs=TOPOLOGY_CRS,
        diagnostic_crs=DIAGNOSTIC_CRS,
        precision_policy_id=str(precision_policy_id).strip(),
        precision_grid=None if precision_grid is None else float(precision_grid),
    )


__all__ = [
    "TOPOLOGY_CRS",
    "DIAGNOSTIC_CRS",
    "DEFAULT_PRECISION_POLICY_ID",
    "TEST_PRECISION_POLICY_ID",
    "ENGINE_FAMILY",
    "detect_runtime_signature",
]
