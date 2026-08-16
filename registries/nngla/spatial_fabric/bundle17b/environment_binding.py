"""Bundle 17B environmental bindings for the 1,104 governed reference-ground points."""
from __future__ import annotations

from functools import lru_cache
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_EVEN

from registries.nngla.spatial_fabric import candidate_identity

from ._shared import SOURCE_ROOT, csv_rows, decimal_text
from .contracts import EnvironmentBinding, EnvironmentEvidenceType

_POINTS = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_spatial_grid_points_v001.csv"
_CELLS = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_spatial_grid_cells_v001.csv"
_ELEVATION = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_elevation_observations_v001.csv"
_CLIMATE = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_climate_observations_v001.csv"
_VEGETATION = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_vegetation_observations_v001.csv"
_HYDRO_VERTICES = SOURCE_ROOT / "02_existing_physical_world" / "novegeo_hydrology_geometry_vertices_v001.csv"
_HYDRO_JUNCTIONS = SOURCE_ROOT / "02_existing_physical_world" / "novegeo_hydrology_junctions_v001.csv"
_RIVERS = SOURCE_ROOT / "02_existing_physical_world" / "novegeo_river_candidates_v001.csv"
_LAKES = SOURCE_ROOT / "02_existing_physical_world" / "novegeo_lake_candidates_v001.csv"


def _nearest(row: dict[str, str], candidates: tuple[dict[str, str], ...]) -> tuple[dict[str, str], Decimal]:
    lon = Decimal(row["longitude"])
    lat = Decimal(row["latitude"])
    best = None
    best_distance_squared = None
    for candidate in candidates:
        dx = lon - Decimal(candidate["longitude"])
        dy = lat - Decimal(candidate["latitude"])
        distance_squared = dx * dx + dy * dy
        tie_key = candidate.get("climate_observation_id") or candidate.get("vegetation_observation_id") or ""
        if best is None or distance_squared < best_distance_squared or (
            distance_squared == best_distance_squared and tie_key < (
                best.get("climate_observation_id") or best.get("vegetation_observation_id") or ""
            )
        ):
            best = candidate
            best_distance_squared = distance_squared
    if best is None or best_distance_squared is None:
        raise ValueError("nearest qualified observation requested from an empty source")
    return best, best_distance_squared.sqrt()


def _distance_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return decimal_text(value.quantize(Decimal("0.000000001"), rounding=ROUND_HALF_EVEN))


def _hydrology_by_coordinate() -> dict[tuple[Decimal, Decimal], tuple[str, ...]]:
    values: dict[tuple[Decimal, Decimal], set[str]] = defaultdict(set)
    for row in csv_rows(_HYDRO_VERTICES):
        values[(Decimal(row["longitude"]), Decimal(row["latitude"]))].add(row["source_feature_id"])
    for row in csv_rows(_HYDRO_JUNCTIONS):
        values[(Decimal(row["longitude"]), Decimal(row["latitude"]))].add(row["junction_id"])
    for row in csv_rows(_RIVERS):
        values[(Decimal(row["reference_longitude"]), Decimal(row["reference_latitude"]))].add(row["source_river_id"])
    for row in csv_rows(_LAKES):
        values[(Decimal(row["reference_longitude"]), Decimal(row["reference_latitude"]))].add(row["source_lake_id"])
    return {key: tuple(sorted(ids)) for key, ids in values.items()}


@lru_cache(maxsize=1)
def derive_environment_bindings() -> tuple[EnvironmentBinding, ...]:
    points = csv_rows(_POINTS)
    cells_by_point = {row["spatial_point_id"]: row for row in csv_rows(_CELLS)}
    elevation_by_point = {row["spatial_point_id"]: row for row in csv_rows(_ELEVATION)}
    climate = csv_rows(_CLIMATE)
    climate_by_point = {row["spatial_point_id"]: row for row in climate}
    vegetation = csv_rows(_VEGETATION)
    vegetation_by_point = {row["spatial_point_id"]: row for row in vegetation}
    hydrology = _hydrology_by_coordinate()
    out: list[EnvironmentBinding] = []

    for index, point in enumerate(points, start=1):
        point_id = point["spatial_point_id"]
        cell = cells_by_point.get(point_id)
        elevation = elevation_by_point.get(point_id)
        if cell is None or elevation is None:
            raise ValueError(f"reference point {point_id} is missing cell/elevation evidence")

        direct_climate = climate_by_point.get(point_id)
        if direct_climate is not None:
            climate_row = direct_climate
            climate_distance = Decimal("0")
            climate_evidence = EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION
        else:
            climate_row, climate_distance = _nearest(point, climate)
            climate_evidence = EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION

        direct_vegetation = vegetation_by_point.get(point_id)
        if direct_vegetation is not None:
            vegetation_row = direct_vegetation
            vegetation_distance = Decimal("0")
            vegetation_evidence = EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION
        else:
            vegetation_row, vegetation_distance = _nearest(point, vegetation)
            vegetation_evidence = EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION

        lon = Decimal(point["longitude"])
        lat = Decimal(point["latitude"])
        hydro_refs = hydrology.get((lon, lat), ())
        hydro_type = (
            EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION if hydro_refs
            else EnvironmentEvidenceType.NOT_AVAILABLE
        )

        out.append(EnvironmentBinding(
            environment_binding_id=f"NG-ENV-BIND-{index:06d}",
            spatial_point_id=point_id,
            spatial_cell_id=cell["spatial_cell_id"],
            coordinate_candidate_id=candidate_identity(lon, lat),
            major_grid_id=point["major_grid_id"],
            sovereign_part_id=point["sovereign_part_id"],
            elevation_observation_id=elevation["elevation_observation_id"],
            elevation_m=elevation["elevation_m"],
            elevation_evidence_type=EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION,
            terrain_class=elevation["terrain_class"],
            terrain_evidence_type=EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION,
            climate_observation_id=climate_row["climate_observation_id"],
            climate_resolution_distance_degrees=_distance_text(climate_distance),
            annual_rainfall_mm=climate_row["annual_rainfall_mm"],
            mean_temperature_c=climate_row["mean_temperature_c"],
            mean_wind_speed_mps=climate_row["mean_wind_speed_mps"],
            prevailing_wind_direction_deg=climate_row["prevailing_wind_direction_deg"],
            climate_class=climate_row["climate_class"],
            climate_evidence_type=climate_evidence,
            vegetation_observation_id=vegetation_row["vegetation_observation_id"],
            vegetation_resolution_distance_degrees=_distance_text(vegetation_distance),
            vegetation_class=vegetation_row["vegetation_class"],
            aridity_class=vegetation_row["aridity_class"],
            vegetation_evidence_type=vegetation_evidence,
            hydrology_reference_id="|".join(hydro_refs),
            hydrology_evidence_type=hydro_type,
            environment_resolution_status="PASS",
            runtime_effect_scope="SHARED_REFERENCE",
        ))
    return tuple(out)


def environment_coverage_rows(bindings: tuple[EnvironmentBinding, ...] | None = None) -> tuple[dict[str, str], ...]:
    current = bindings or derive_environment_bindings()
    rows = []
    for item in current:
        evidence = (
            item.elevation_evidence_type, item.terrain_evidence_type,
            item.climate_evidence_type, item.climate_evidence_type, item.climate_evidence_type,
            item.vegetation_evidence_type, item.vegetation_evidence_type, item.hydrology_evidence_type,
        )
        counts = {kind: sum(value is kind for value in evidence) for kind in EnvironmentEvidenceType}
        rows.append({
            "spatial_reference_id": item.spatial_point_id,
            "coordinate_candidate_id": item.coordinate_candidate_id,
            "elevation_status": "DIRECT",
            "terrain_status": "DIRECT",
            "climate_status": "DIRECT" if item.climate_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "rainfall_status": "DIRECT" if item.climate_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "temperature_status": "DIRECT" if item.climate_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "wind_status": "DIRECT" if item.climate_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "vegetation_status": "DIRECT" if item.vegetation_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "aridity_status": "DIRECT" if item.vegetation_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NEAREST_QUALIFIED",
            "hydrology_status": "DIRECT" if item.hydrology_evidence_type is EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION else "NOT_AVAILABLE_AT_POINT",
            "direct_evidence_count": str(counts[EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION]),
            "derived_evidence_count": str(counts[EnvironmentEvidenceType.GOVERNED_DERIVATION]),
            "nearest_evidence_count": str(counts[EnvironmentEvidenceType.NEAREST_QUALIFIED_OBSERVATION]),
            "missing_evidence_count": str(counts[EnvironmentEvidenceType.NOT_AVAILABLE]),
            "overall_coverage_status": "PASS",
            "findings": "HYDROLOGY_ABSENCE_IS_NOT_INFERRED" if item.hydrology_evidence_type is EnvironmentEvidenceType.NOT_AVAILABLE else "",
        })
    return tuple(rows)


def environment_binding_findings(bindings: tuple[EnvironmentBinding, ...] | None = None) -> tuple[str, ...]:
    current = bindings or derive_environment_bindings()
    findings: list[str] = []
    for item in current:
        if item.environment_resolution_status != "PASS":
            findings.append(f"ENVIRONMENT_BINDING_FAILED:{item.spatial_point_id}")
        if item.elevation_evidence_type is not EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION:
            findings.append(f"ELEVATION_NOT_DIRECT:{item.spatial_point_id}")
        if item.terrain_evidence_type is not EnvironmentEvidenceType.DIRECT_SOURCE_OBSERVATION:
            findings.append(f"TERRAIN_NOT_DIRECT:{item.spatial_point_id}")
    return tuple(findings)


__all__ = ["derive_environment_bindings", "environment_coverage_rows", "environment_binding_findings"]
