"""Versioned equirectangular world projection shared with the browser."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import GeographicCoordinate, ProjectedCoordinate


@dataclass(frozen=True, slots=True)
class EquirectangularWorldProjection:
    projection_id: str = "projection:novegeo:equirectangular-world"
    version: int = 1
    tolerance: float = 1e-8

    def forward(self, coordinate: GeographicCoordinate) -> ProjectedCoordinate:
        return ProjectedCoordinate(
            x=(coordinate.longitude + 180.0) / 360.0,
            y=(90.0 - coordinate.latitude) / 180.0,
            projection_id=self.projection_id,
            projection_version=self.version,
        )

    def inverse(self, coordinate: ProjectedCoordinate) -> GeographicCoordinate:
        if coordinate.projection_id != self.projection_id or coordinate.projection_version != self.version:
            raise ValueError("projected coordinate uses an incompatible projection contract")
        if not 0.0 <= coordinate.x <= 1.0 or not 0.0 <= coordinate.y <= 1.0:
            raise ValueError("normalized projected coordinates must be between zero and one")
        return GeographicCoordinate(
            longitude=coordinate.x * 360.0 - 180.0,
            latitude=90.0 - coordinate.y * 180.0,
        )
