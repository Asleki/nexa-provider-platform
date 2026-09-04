"""P006.7.11.15.7.2 governed CITY augmentation for the national-map read path.

This module is intentionally additive.  It consumes only the new public CITY
view created by P006.7.11.15.7.1 and treats that view as authoritative for the
eight official NoveGeo CITY identities.  Historical generic projection copies
for those identities are suppressed rather than used as fallback geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable

from infrastructure.database.read.nngla_national_map import (
    MAP_FAMILIES,
    MapBounds,
    NationalMapFeature,
    NationalMapPage,
    NNGLAMapReadAuthorityError,
)
from infrastructure.database.runtime.read_materialization import (
    current_request_read_materialization,
    materialization_key,
)

CITY_PUBLIC_VIEW = "geography.nngla_city_public_read_v1"
CITY_FAMILY = "ADMINISTRATIVE_AREA"
CITY_CLASSIFICATION_SCHEME = "NNGLA_ADMIN_TYPE"
CITY_CLASSIFICATION_CODE = "CITY"
CITY_LABEL_POINT_ALGORITHM_ID = "algorithm:nngla:city-label-point-on-surface:epsg4326"
CITY_LABEL_POINT_ALGORITHM_VERSION = 1

OFFICIAL_NOVEGEO_CITY_IDS = (
    "NG-ADM-000009",  # Orivane
    "NG-ADM-000032",  # Northgate
    "NG-ADM-000055",  # Vondara
    "NG-ADM-000078",  # Silvermere
    "NG-ADM-000101",  # Tekharo
    "NG-ADM-000124",  # Redhaven
    "NG-ADM-000147",  # Lysora
    "NG-ADM-000170",  # Port Meridian
)
_OFFICIAL_CITY_SET = frozenset(OFFICIAL_NOVEGEO_CITY_IDS)
_CITY_RECORDS_MATERIALIZATION_NAMESPACE = "nngla.city.public_map.records.v1"


@dataclass(frozen=True, slots=True)
class CityMapMetadata:
    subject_id: str
    parent_region_id: str
    label_point: dict[str, object]
    area_m2: float
    perimeter_m: float
    label_point_algorithm_id: str = CITY_LABEL_POINT_ALGORITHM_ID
    label_point_algorithm_version: int = CITY_LABEL_POINT_ALGORITHM_VERSION
    source_view: str = CITY_PUBLIC_VIEW

    def as_public_fields(self) -> dict[str, object]:
        return {
            "administrativeLevel": CITY_CLASSIFICATION_CODE,
            "parentRegionId": self.parent_region_id,
            "labelPoint": self.label_point,
            "labelAnchorKind": "DERIVED_PRESENTATION",
            "labelPointAlgorithmId": self.label_point_algorithm_id,
            "labelPointAlgorithmVersion": self.label_point_algorithm_version,
            "areaM2": self.area_m2,
            "perimeterM": self.perimeter_m,
        }


@dataclass(frozen=True, slots=True)
class CityMapRecord:
    feature: NationalMapFeature
    metadata: CityMapMetadata


class PostgreSQLCityPublicMapRepository:
    """Read zero to eight governed public CITY records from the new CITY view."""

    def __init__(self, pool: Any, *, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        normalized = str(runtime_mode).strip().lower()
        if normalized not in {"simulation", "production"}:
            raise ValueError("runtime_mode must be simulation or production")
        self.pool = pool
        self.runtime_mode = normalized

    @staticmethod
    def _json_object(value: object, label: str) -> dict[str, object]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        raise NNGLAMapReadAuthorityError(f"{label} is malformed")

    def _records(self, *, bounds: MapBounds | None = None) -> tuple[CityMapRecord, ...]:
        bounds_filter = ""
        params: list[object] = []
        if bounds is not None:
            bounds_filter = "AND ST_Intersects(v.geometry,ST_MakeEnvelope(%s,%s,%s,%s,4326))"
            params.extend(
                [
                    bounds.min_longitude,
                    bounds.min_latitude,
                    bounds.max_longitude,
                    bounds.max_latitude,
                ]
            )

        sql = f"""
            SELECT v.city_id,v.parent_region_id,v.canonical_name,v.publication_id,1,
                   v.city_geometry_id,1,'ADMINISTRATIVE_BOUNDARY',
                   v.geometry_type_code,v.crs_code,
                   ST_AsGeoJSON(v.geometry,8)::jsonb,
                   'SHARED_REFERENCE',1,
                   jsonb_build_object(
                     'type','Point',
                     'coordinates',jsonb_build_array(v.label_longitude,v.label_latitude)
                   ),
                   v.area_m2,v.perimeter_m
            FROM {CITY_PUBLIC_VIEW} v
            WHERE v.administrative_type_code='CITY'
              AND v.qualification_status='QUALIFIED'
              AND v.publication_status='PUBLISHED'
              {bounds_filter}
            ORDER BY v.city_id
        """

        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = list(cursor.fetchall())

        records: list[CityMapRecord] = []
        seen: set[str] = set()
        for row in rows:
            subject_id = str(row[0])
            if subject_id not in _OFFICIAL_CITY_SET:
                raise NNGLAMapReadAuthorityError(
                    f"public CITY view exposed unknown CITY identity: {subject_id}"
                )
            if subject_id in seen:
                raise NNGLAMapReadAuthorityError(
                    f"public CITY view returned duplicate CITY identity: {subject_id}"
                )
            seen.add(subject_id)

            parent_region_id = str(row[1])
            if not parent_region_id.startswith("NG-ADM-"):
                raise NNGLAMapReadAuthorityError("CITY parent REGION identity is malformed")

            geometry = self._json_object(row[10], "CITY geometry GeoJSON")
            label_point = self._json_object(row[13], "CITY label point GeoJSON")
            geometry_type = str(row[8]).upper()
            expected = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
            if geometry.get("type") != expected:
                raise NNGLAMapReadAuthorityError("CITY geometry type metadata does not match GeoJSON")
            if label_point.get("type") != "Point":
                raise NNGLAMapReadAuthorityError("CITY label point must be GeoJSON Point")

            area_m2 = float(row[14])
            perimeter_m = float(row[15])
            if not area_m2 > 0 or not perimeter_m > 0:
                raise NNGLAMapReadAuthorityError("CITY measurements must be positive")

            feature = NationalMapFeature(
                subject_id=subject_id,
                family=CITY_FAMILY,
                display_name=str(row[2]),
                publication_reference=str(row[3]),
                geometry_id=str(row[5]),
                geometry_version=int(row[6]),
                geometry_role=str(row[7]),
                geometry_type=geometry_type,
                crs_code=str(row[9]),
                geometry=geometry,
                runtime_effect_scope=str(row[11]),
                classification_scheme=CITY_CLASSIFICATION_SCHEME,
                classification_code=CITY_CLASSIFICATION_CODE,
                read_model_version=max(1, int(row[12])),
            )
            metadata = CityMapMetadata(
                subject_id=subject_id,
                parent_region_id=parent_region_id,
                label_point=label_point,
                area_m2=area_m2,
                perimeter_m=perimeter_m,
            )
            records.append(CityMapRecord(feature=feature, metadata=metadata))
        result = tuple(records)
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            materialization.merge_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_RECORDS_MATERIALIZATION_NAMESPACE,
                ),
                {record.feature.subject_id: record for record in result},
            )
        return result

    def list_features(
        self,
        *,
        bounds: MapBounds,
        families: Iterable[str] = MAP_FAMILIES,
        limit: int = 500,
        after: tuple[str, str] | None = None,
    ) -> NationalMapPage:
        selected = tuple(dict.fromkeys(str(value).strip().upper() for value in families))
        if not selected or any(value not in MAP_FAMILIES for value in selected):
            raise ValueError("at least one supported map family is required")
        if not 1 <= int(limit) <= 2000:
            raise ValueError("limit must be between 1 and 2000")
        if CITY_FAMILY not in selected:
            return NationalMapPage((), False, None, 1)

        features = [record.feature for record in self._records(bounds=bounds)]
        if after is not None:
            features = [
                feature
                for feature in features
                if (feature.family, feature.subject_id) > tuple(after)
            ]
        has_more = len(features) > int(limit)
        page_items = tuple(features[: int(limit)])
        last_key = (
            (page_items[-1].family, page_items[-1].subject_id)
            if has_more and page_items
            else None
        )
        read_model_version = max((item.read_model_version for item in page_items), default=1)
        return NationalMapPage(page_items, has_more, last_key, read_model_version)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized not in _OFFICIAL_CITY_SET:
            return None
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            cached = materialization.complete_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_RECORDS_MATERIALIZATION_NAMESPACE,
                ),
                (normalized,),
            )
            if cached is not None:
                return cached[normalized].feature
        for record in self._records(bounds=None):
            if record.feature.subject_id == normalized:
                return record.feature
        return None

    def metadata_for_subjects(self, subject_ids: Iterable[str]) -> dict[str, CityMapMetadata]:
        wanted = {str(value) for value in subject_ids if str(value) in _OFFICIAL_CITY_SET}
        if not wanted:
            return {}
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            cached = materialization.complete_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_RECORDS_MATERIALIZATION_NAMESPACE,
                ),
                wanted,
            )
            if cached is not None:
                return {
                    subject_id: record.metadata
                    for subject_id, record in cached.items()
                }
        return {
            record.feature.subject_id: record.metadata
            for record in self._records(bounds=None)
            if record.feature.subject_id in wanted
        }


class CityAugmentedNNGLANationalMapRepository:
    """Merge new CITY authority after the already-augmented national map repository."""

    def __init__(self, base_repository: Any, city_repository: PostgreSQLCityPublicMapRepository) -> None:
        if base_repository is None or city_repository is None:
            raise TypeError("base_repository and city_repository are required")
        if str(base_repository.runtime_mode) != str(city_repository.runtime_mode):
            raise ValueError("base and CITY repositories must use the same runtime_mode")
        self.base_repository = base_repository
        self.city_repository = city_repository
        self.runtime_mode = str(base_repository.runtime_mode)

    def list_features(
        self,
        *,
        bounds: MapBounds,
        families: Iterable[str] = MAP_FAMILIES,
        limit: int = 500,
        after: tuple[str, str] | None = None,
    ) -> NationalMapPage:
        base_fetch_limit = min(2000, int(limit) + len(OFFICIAL_NOVEGEO_CITY_IDS))
        base_page = self.base_repository.list_features(
            bounds=bounds,
            families=families,
            limit=base_fetch_limit,
            after=after,
        )
        city_page = self.city_repository.list_features(
            bounds=bounds,
            families=families,
            limit=min(8, int(limit)),
            after=after,
        )

        # For the official CITY identities the new CITY public view is the sole
        # authority.  Suppress any historical generic ADMINISTRATIVE_AREA copy
        # even while a CITY is unpublished/withdrawn, preventing stale fallback.
        merged: dict[tuple[str, str], NationalMapFeature] = {
            (item.family, item.subject_id): item
            for item in base_page.items
            if not (
                item.family == CITY_FAMILY
                and item.subject_id in _OFFICIAL_CITY_SET
            )
        }
        for item in city_page.items:
            merged[(item.family, item.subject_id)] = item

        ordered = sorted(merged.values(), key=lambda item: (item.family, item.subject_id))
        has_more = base_page.has_more or city_page.has_more or len(ordered) > int(limit)
        page_items = tuple(ordered[: int(limit)])
        last_key = (
            (page_items[-1].family, page_items[-1].subject_id)
            if has_more and page_items
            else None
        )
        read_model_version = max(
            [base_page.read_model_version, city_page.read_model_version]
            + [item.read_model_version for item in page_items]
        )
        return NationalMapPage(page_items, has_more, last_key, read_model_version)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized in _OFFICIAL_CITY_SET:
            return self.city_repository.get_subject(normalized)
        return self.base_repository.get_subject(normalized)


__all__ = [
    "CITY_PUBLIC_VIEW",
    "CITY_FAMILY",
    "CITY_CLASSIFICATION_SCHEME",
    "CITY_CLASSIFICATION_CODE",
    "CITY_LABEL_POINT_ALGORITHM_ID",
    "CITY_LABEL_POINT_ALGORITHM_VERSION",
    "OFFICIAL_NOVEGEO_CITY_IDS",
    "CityMapMetadata",
    "CityMapRecord",
    "PostgreSQLCityPublicMapRepository",
    "CityAugmentedNNGLANationalMapRepository",
]
