"""Read-only source catalogue for the .15.5 spatial realization engine.

The module deliberately consumes locked Bundle 19A/19B evidence.  It does not
mutate or reinterpret those milestones; it exposes a stable selection-oriented
view suitable for later reconciliation and live execution.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from registries.nngla.spatial_fabric.bundle19a._shared import (
    FOOTPRINTS_PATH,
    REFERENCE_POINTS_PATH,
    PLACE_DATASET_ID,
    PLACE_DATASET_VERSION,
)
from registries.nngla.spatial_fabric.bundle19a.footprints import derive_settlement_footprints
from registries.nngla.spatial_fabric.bundle19a.persistence import footprint_geojson, point_geojson
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points
from registries.nngla.spatial_fabric.bundle19a.source import load_settlement_requirements
from registries.nngla.spatial_fabric.bundle19b._shared import (
    BOUNDARIES,
    DATASET_ID as ADMIN_DATASET_ID,
    DATASET_VERSION as ADMIN_DATASET_VERSION,
    LEGALIZATION_DECISIONS,
    QUALIFICATION_RESULTS,
    TOPOLOGY_POLICY,
    TOPOLOGY_RELATIONSHIPS,
)
from registries.nngla.spatial_fabric.bundle19b.authoring import load_boundary_candidates

from .contracts import (
    CityRoot,
    FabricInput,
    FabricInputRole,
    GeometryCandidate,
    GeometryEncoding,
    GeometryRole,
    SpatialSeed,
    SubjectType,
)

ROOT = Path(__file__).resolve().parents[3]
PLAN_SOURCE_ID = "P006.7.11.15.5"


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _checksum_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _sha256_path(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def source_hashes() -> tuple[tuple[str, str], ...]:
    paths = (
        REFERENCE_POINTS_PATH,
        FOOTPRINTS_PATH,
        BOUNDARIES,
        TOPOLOGY_POLICY,
        TOPOLOGY_RELATIONSHIPS,
        QUALIFICATION_RESULTS,
        LEGALIZATION_DECISIONS,
    )
    rows = []
    for path in paths:
        rows.append((path.relative_to(ROOT).as_posix(), _sha256_path(path)))
    return tuple(sorted(rows))


@lru_cache(maxsize=1)
def aggregate_source_sha256() -> str:
    return _checksum_text(_canonical_json(source_hashes()))


@lru_cache(maxsize=1)
def _place_point_candidates() -> dict[str, GeometryCandidate]:
    out: dict[str, GeometryCandidate] = {}
    for point in derive_place_reference_points():
        payload = _canonical_json(point_geojson(point))
        out[point.place_id] = GeometryCandidate(
            root_place_id=point.place_id,
            subject_type=SubjectType.PLACE,
            subject_id=point.place_id,
            geometry_role=GeometryRole.PLACE_REFERENCE_POINT,
            source_candidate_id=point.reference_candidate_id,
            geometry_type_code="POINT",
            encoding=GeometryEncoding.GEOJSON,
            payload=payload,
            checksum_sha256=_checksum_text(payload),
            reservation_key=point.geometry_reservation_key,
            source_dataset_id=PLACE_DATASET_ID,
            source_dataset_version=PLACE_DATASET_VERSION,
            source_path_reference=REFERENCE_POINTS_PATH.relative_to(ROOT).as_posix(),
        )
    if len(out) != 700:
        raise ValueError(".15.5 requires the complete locked 700-place Bundle 19A point catalogue")
    return out


@lru_cache(maxsize=1)
def _place_footprint_candidates() -> dict[str, GeometryCandidate]:
    out: dict[str, GeometryCandidate] = {}
    for footprint in derive_settlement_footprints():
        payload = _canonical_json(footprint_geojson(footprint))
        out[footprint.place_id] = GeometryCandidate(
            root_place_id=footprint.place_id,
            subject_type=SubjectType.PLACE,
            subject_id=footprint.place_id,
            geometry_role=GeometryRole.SETTLEMENT_FOOTPRINT,
            source_candidate_id=footprint.footprint_candidate_id,
            geometry_type_code="POLYGON",
            encoding=GeometryEncoding.GEOJSON,
            payload=payload,
            checksum_sha256=_checksum_text(payload),
            reservation_key=footprint.geometry_reservation_key,
            source_dataset_id=PLACE_DATASET_ID,
            source_dataset_version=PLACE_DATASET_VERSION,
            source_path_reference=FOOTPRINTS_PATH.relative_to(ROOT).as_posix(),
        )
    return out


@lru_cache(maxsize=1)
def _administrative_candidates():
    """Index the locked Bundle 19B authoring records by canonical admin identity.

    Administrative boundaries may participate in more than one selected-root
    closure as validation context.  The cached source record therefore remains
    root-neutral; a root-scoped :class:`GeometryCandidate` is constructed only
    when a planner asks for one.  This prevents any major city from becoming a
    hidden production default.
    """
    out = {
        candidate.administrative_area_id: candidate
        for candidate in load_boundary_candidates()
    }
    if len(out) != 192:
        raise ValueError(".15.5 requires the complete locked 192-boundary Bundle 19B catalogue")
    return out


@lru_cache(maxsize=1)
def _reference_points_by_source_code():
    return {row.source_place_code: row for row in derive_place_reference_points()}


def administrative_reference_seed(administrative_area_id: str) -> SpatialSeed:
    try:
        admin = _administrative_candidates()[administrative_area_id]
    except KeyError as exc:
        raise KeyError(f"unknown administrative boundary {administrative_area_id}") from exc
    point = _reference_points_by_source_code().get(admin.source_record_id)
    if point is None:
        raise ValueError(f"canonical reference point missing for administrative area {administrative_area_id}")
    return SpatialSeed(
        subject_id=administrative_area_id,
        source_place_code=admin.source_record_id,
        place_id=point.place_id,
        longitude=float(point.longitude),
        latitude=float(point.latitude),
    )


def administrative_reference_seeds(administrative_area_ids) -> tuple[SpatialSeed, ...]:
    rows = tuple(administrative_reference_seed(value) for value in administrative_area_ids)
    if len({row.subject_id for row in rows}) != len(rows):
        raise ValueError("administrative reference seed identities must be unique")
    return rows


def geometry_for_admin(administrative_area_id: str, root_place_id: str) -> GeometryCandidate:
    try:
        candidate = _administrative_candidates()[administrative_area_id]
    except KeyError as exc:
        raise KeyError(f"unknown administrative boundary {administrative_area_id}") from exc
    payload = _canonical_json(candidate.geometry)
    return GeometryCandidate(
        root_place_id=root_place_id,
        subject_type=SubjectType.ADMINISTRATIVE_AREA,
        subject_id=candidate.administrative_area_id,
        geometry_role=GeometryRole.ADMINISTRATIVE_BOUNDARY,
        source_candidate_id=candidate.boundary_candidate_id,
        geometry_type_code=candidate.geometry_type_code,
        encoding=GeometryEncoding.GEOJSON,
        payload=payload,
        checksum_sha256=_checksum_text(payload),
        reservation_key=candidate.geometry_reservation_key,
        source_dataset_id=ADMIN_DATASET_ID,
        source_dataset_version=ADMIN_DATASET_VERSION,
        source_path_reference=BOUNDARIES.relative_to(ROOT).as_posix(),
    )


@lru_cache(maxsize=1)
def city_roots() -> tuple[CityRoot, ...]:
    requirements = load_settlement_requirements()
    admins = load_boundary_candidates()
    admin_by_source = {row.source_record_id: row for row in admins}
    roots: list[CityRoot] = []
    for place in requirements:
        if place.place_type_code != "CITY":
            continue
        admin = admin_by_source.get(place.source_place_code)
        if admin is None or admin.administrative_type_code != "CITY":
            raise ValueError(f"major-city administrative counterpart missing for {place.place_id}")
        if not admin.parent_administrative_area_id:
            raise ValueError(f"major city has no administrative validation parent: {place.place_id}")
        roots.append(CityRoot(
            place_id=place.place_id,
            source_place_code=place.source_place_code,
            canonical_name=place.canonical_name,
            region_code=place.region_code,
            administrative_area_id=admin.administrative_area_id,
            validation_parent_id=admin.parent_administrative_area_id,
        ))
    roots.sort(key=lambda row: int(row.place_id.rsplit("-", 1)[1]))
    if len(roots) != 8:
        raise ValueError(f"current NoveGeo major-city catalogue must contain exactly eight roots, found {len(roots)}")
    if len({root.region_code for root in roots}) != 8:
        raise ValueError("major-city roots must remain one-per-region in the current source model")
    return tuple(roots)


@lru_cache(maxsize=1)
def city_root_by_id() -> dict[str, CityRoot]:
    return {row.place_id: row for row in city_roots()}


def place_point_candidate(place_id: str) -> GeometryCandidate:
    return _place_point_candidates()[place_id]


def place_footprint_candidate(place_id: str) -> GeometryCandidate | None:
    return _place_footprint_candidates().get(place_id)


def administrative_source_rows():
    return load_boundary_candidates()


def administrative_row(administrative_area_id: str):
    """Return one frozen Bundle-19B administrative candidate by canonical identity."""
    try:
        return _administrative_candidates()[administrative_area_id]
    except KeyError as exc:
        raise KeyError(f"unknown administrative boundary {administrative_area_id}") from exc


def administrative_children(parent_administrative_area_id: str):
    """Return direct frozen administrative children in canonical identity order."""
    rows = [
        row for row in _administrative_candidates().values()
        if row.parent_administrative_area_id == parent_administrative_area_id
    ]
    return tuple(sorted(rows, key=lambda item: int(item.administrative_area_id.rsplit("-", 1)[1])))


def administrative_input(administrative_area_id: str, input_role: FabricInputRole) -> FabricInput:
    """Build a hash-bound fabric input reference without changing the source record."""
    row = administrative_row(administrative_area_id)
    payload = _canonical_json(row.geometry)
    return FabricInput(
        input_role=input_role,
        subject_id=row.administrative_area_id,
        administrative_type_code=row.administrative_type_code,
        canonical_name=row.canonical_name,
        source_candidate_id=row.boundary_candidate_id,
        geometry_checksum_sha256=_checksum_text(payload),
        source_path_reference=BOUNDARIES.relative_to(ROOT).as_posix(),
    )


def administrative_geometry_payload(administrative_area_id: str) -> str:
    """Canonical frozen GeoJSON text used by the read-only shared-face prototype."""
    return _canonical_json(administrative_row(administrative_area_id).geometry)


def reference_point_support(place_id: str) -> str:
    by_id = {row.place_id: row for row in derive_place_reference_points()}
    return by_id[place_id].supporting_spatial_point_id


__all__ = [
    "PLAN_SOURCE_ID",
    "source_hashes",
    "aggregate_source_sha256",
    "city_roots",
    "city_root_by_id",
    "place_point_candidate",
    "place_footprint_candidate",
    "geometry_for_admin",
    "administrative_reference_seed",
    "administrative_reference_seeds",
    "administrative_source_rows",
    "administrative_row",
    "administrative_children",
    "administrative_input",
    "administrative_geometry_payload",
    "reference_point_support",
]
