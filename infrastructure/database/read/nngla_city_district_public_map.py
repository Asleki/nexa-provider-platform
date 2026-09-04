"""P006.7.11.15.9.2 governed CITY_DISTRICT augmentation for national-map reads."""
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

CITY_DISTRICT_PUBLIC_VIEW = "geography.nngla_city_district_public_read_v2"
CITY_DISTRICT_FAMILY = "ADMINISTRATIVE_AREA"
CITY_DISTRICT_CLASSIFICATION_SCHEME = "NNGLA_ADMIN_TYPE"
CITY_DISTRICT_CLASSIFICATION_CODE = "CITY_DISTRICT"
CITY_DISTRICT_LABEL_POINT_ALGORITHM_ID = (
    "algorithm:nngla:city-district-label-point-on-surface:epsg4326"
)
CITY_DISTRICT_LABEL_POINT_ALGORITHM_VERSION = 1
_CITY_DISTRICT_GOVERNED_IDS_MATERIALIZATION_NAMESPACE = (
    "nngla.city_district.governed_ids.v2"
)
_CITY_DISTRICT_RECORDS_MATERIALIZATION_NAMESPACE = (
    "nngla.city_district.public_map.records.v2"
)


@dataclass(frozen=True, slots=True)
class CityDistrictMapMetadata:
    subject_id: str
    parent_city_id: str
    region_code: str
    label_point: dict[str, object]
    area_m2: float
    perimeter_m: float
    partition_qualification_id: str | None
    partition_status: str
    source_administrative_type_code: str
    label_point_algorithm_id: str = CITY_DISTRICT_LABEL_POINT_ALGORITHM_ID
    label_point_algorithm_version: int = CITY_DISTRICT_LABEL_POINT_ALGORITHM_VERSION
    source_view: str = CITY_DISTRICT_PUBLIC_VIEW

    def as_public_fields(self) -> dict[str, object]:
        return {
            "administrativeLevel": CITY_DISTRICT_CLASSIFICATION_CODE,
            "parentCityId": self.parent_city_id,
            "regionCode": self.region_code,
            "labelPoint": self.label_point,
            "labelAnchorKind": "DERIVED_PRESENTATION",
            "labelPointAlgorithmId": self.label_point_algorithm_id,
            "labelPointAlgorithmVersion": self.label_point_algorithm_version,
            "areaM2": self.area_m2,
            "perimeterM": self.perimeter_m,
            "partitionQualificationId": self.partition_qualification_id,
            "partitionStatus": self.partition_status,
            "sourceAdministrativeTypeCode": self.source_administrative_type_code,
        }


@dataclass(frozen=True, slots=True)
class CityDistrictMapRecord:
    feature: NationalMapFeature
    metadata: CityDistrictMapMetadata


class PostgreSQLCityDistrictPublicMapRepository:
    def __init__(self, pool: Any, *, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        normalized = str(runtime_mode).strip().lower()
        if normalized not in {"simulation", "production"}:
            raise ValueError("runtime_mode must be simulation or production")
        self.pool = pool
        self.runtime_mode = normalized

    def governed_ids(self) -> frozenset[str]:
        """Return only DISTRICT identities whose declared parent is a CITY."""
        materialization = current_request_read_materialization(self.pool)
        cache_key = materialization_key(
            self.runtime_mode,
            _CITY_DISTRICT_GOVERNED_IDS_MATERIALIZATION_NAMESPACE,
        )
        if materialization is not None:
            cached = materialization.get(cache_key)
            if isinstance(cached, frozenset):
                return cached

        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT child.administrative_area_id
                    FROM geography.nngla_administrative_area AS child
                    JOIN geography.nngla_administrative_area AS parent
                      ON parent.source_record_id=child.parent_source_record_id
                    WHERE child.administrative_type_code IN ('DISTRICT','CITY_DISTRICT')
                      AND parent.administrative_type_code='CITY'
                    ORDER BY child.administrative_area_id
                    """
                )
                ids = tuple(str(row[0]) for row in cursor.fetchall())
        if not ids or len(set(ids)) != len(ids):
            raise NNGLAMapReadAuthorityError(
                "governed CITY_DISTRICT identity set must be non-empty and unique"
            )
        governed = frozenset(ids)
        if materialization is not None:
            materialization.set(cache_key, governed)
        return governed

    @staticmethod
    def _json_object(value: object, label: str) -> dict[str, object]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        raise NNGLAMapReadAuthorityError(f"{label} is malformed")

    def _records(
        self,
        *,
        bounds: MapBounds | None = None,
    ) -> tuple[CityDistrictMapRecord, ...]:
        bounds_filter = ""
        params: list[object] = []
        if bounds is not None:
            bounds_filter = (
                "AND ST_Intersects(v.geometry,ST_MakeEnvelope(%s,%s,%s,%s,4326))"
            )
            params.extend(
                [
                    bounds.min_longitude,
                    bounds.min_latitude,
                    bounds.max_longitude,
                    bounds.max_latitude,
                ]
            )

        sql = f"""
            SELECT v.district_id,v.parent_city_id,v.region_code,v.canonical_name,
                   v.administrative_type_code,v.publication_id,v.district_geometry_id,
                   v.realization_version,v.geometry_type_code,v.crs_code,
                   ST_AsGeoJSON(v.geometry,8)::jsonb,
                   jsonb_build_object(
                     'type','Point',
                     'coordinates',jsonb_build_array(v.label_longitude,v.label_latitude)
                   ),
                   v.area_m2,v.perimeter_m,
                   v.partition_qualification_id,v.partition_status
            FROM {CITY_DISTRICT_PUBLIC_VIEW} AS v
            WHERE v.publication_status='PUBLISHED'
              {bounds_filter}
            ORDER BY v.district_id
        """
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = list(cursor.fetchall())

        governed = self.governed_ids()
        records: list[CityDistrictMapRecord] = []
        seen: set[str] = set()
        for row in rows:
            subject_id = str(row[0])
            if subject_id not in governed:
                raise NNGLAMapReadAuthorityError(
                    f"public CITY_DISTRICT view exposed unknown identity: {subject_id}"
                )
            if subject_id in seen:
                raise NNGLAMapReadAuthorityError(
                    f"public CITY_DISTRICT view returned duplicate identity: {subject_id}"
                )
            seen.add(subject_id)
            parent_city_id = str(row[1])
            if not parent_city_id.startswith("NG-ADM-"):
                raise NNGLAMapReadAuthorityError(
                    "CITY_DISTRICT parent CITY identity is malformed"
                )
            geometry = self._json_object(row[10], "CITY_DISTRICT geometry GeoJSON")
            label_point = self._json_object(row[11], "CITY_DISTRICT label point GeoJSON")
            geometry_type = str(row[8]).upper()
            expected_type = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
            if geometry.get("type") != expected_type:
                raise NNGLAMapReadAuthorityError(
                    "CITY_DISTRICT geometry type metadata does not match GeoJSON"
                )
            if label_point.get("type") != "Point":
                raise NNGLAMapReadAuthorityError(
                    "CITY_DISTRICT label point must be GeoJSON Point"
                )
            area_m2 = float(row[12])
            perimeter_m = float(row[13])
            if area_m2 <= 0 or perimeter_m <= 0:
                raise NNGLAMapReadAuthorityError(
                    "CITY_DISTRICT measurements must be positive"
                )
            partition_status = str(row[15]).upper()
            if partition_status not in {"PARTIAL", "COMPLETE"}:
                raise NNGLAMapReadAuthorityError(
                    "CITY_DISTRICT fabric status must be PARTIAL or COMPLETE"
                )
            feature = NationalMapFeature(
                subject_id=subject_id,
                family=CITY_DISTRICT_FAMILY,
                display_name=str(row[3]),
                publication_reference=str(row[5]),
                geometry_id=str(row[6]),
                geometry_version=max(1, int(row[7])),
                geometry_role="ADMINISTRATIVE_BOUNDARY",
                geometry_type=geometry_type,
                crs_code=str(row[9]),
                geometry=geometry,
                runtime_effect_scope="SHARED_REFERENCE",
                classification_scheme=CITY_DISTRICT_CLASSIFICATION_SCHEME,
                classification_code=CITY_DISTRICT_CLASSIFICATION_CODE,
                read_model_version=1,
            )
            metadata = CityDistrictMapMetadata(
                subject_id=subject_id,
                parent_city_id=parent_city_id,
                region_code=str(row[2]),
                label_point=label_point,
                area_m2=area_m2,
                perimeter_m=perimeter_m,
                partition_qualification_id=(None if row[14] is None else str(row[14])),
                partition_status=partition_status,
                source_administrative_type_code=str(row[4]).upper(),
            )
            records.append(CityDistrictMapRecord(feature=feature, metadata=metadata))
        result = tuple(records)
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            materialization.merge_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_DISTRICT_RECORDS_MATERIALIZATION_NAMESPACE,
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
        if CITY_DISTRICT_FAMILY not in selected:
            return NationalMapPage((), False, None, 1)

        features = [record.feature for record in self._records(bounds=bounds)]
        if after is not None:
            features = [
                feature
                for feature in features
                if (feature.family, feature.subject_id) > tuple(after)
            ]
        has_more = len(features) > int(limit)
        items = tuple(features[: int(limit)])
        last_key = (
            (items[-1].family, items[-1].subject_id)
            if has_more and items
            else None
        )
        return NationalMapPage(
            items,
            has_more,
            last_key,
            max((item.read_model_version for item in items), default=1),
        )

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized not in self.governed_ids():
            return None
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            cached = materialization.complete_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_DISTRICT_RECORDS_MATERIALIZATION_NAMESPACE,
                ),
                (normalized,),
            )
            if cached is not None:
                return cached[normalized].feature
        for record in self._records(bounds=None):
            if record.feature.subject_id == normalized:
                return record.feature
        return None

    def metadata_for_subjects(
        self,
        subject_ids: Iterable[str],
    ) -> dict[str, CityDistrictMapMetadata]:
        governed = self.governed_ids()
        wanted = {str(value) for value in subject_ids if str(value) in governed}
        if not wanted:
            return {}
        materialization = current_request_read_materialization(self.pool)
        if materialization is not None:
            cached = materialization.complete_mapping(
                materialization_key(
                    self.runtime_mode,
                    _CITY_DISTRICT_RECORDS_MATERIALIZATION_NAMESPACE,
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


class CityDistrictAugmentedNNGLANationalMapRepository:
    def __init__(
        self,
        base_repository: Any,
        city_district_repository: PostgreSQLCityDistrictPublicMapRepository,
    ) -> None:
        if base_repository is None or city_district_repository is None:
            raise TypeError("base_repository and city_district_repository are required")
        if str(base_repository.runtime_mode) != str(city_district_repository.runtime_mode):
            raise ValueError(
                "base and CITY_DISTRICT repositories must use the same runtime_mode"
            )
        self.base_repository = base_repository
        self.city_district_repository = city_district_repository
        self.runtime_mode = str(base_repository.runtime_mode)

    def list_features(
        self,
        *,
        bounds: MapBounds,
        families: Iterable[str] = MAP_FAMILIES,
        limit: int = 500,
        after: tuple[str, str] | None = None,
    ) -> NationalMapPage:
        governed = self.city_district_repository.governed_ids()
        base_page = self.base_repository.list_features(
            bounds=bounds,
            families=families,
            limit=min(2000, int(limit) + len(governed)),
            after=after,
        )
        district_page = self.city_district_repository.list_features(
            bounds=bounds,
            families=families,
            limit=int(limit),
            after=after,
        )

        merged: dict[tuple[str, str], NationalMapFeature] = {
            (item.family, item.subject_id): item
            for item in base_page.items
            if not (
                item.family == CITY_DISTRICT_FAMILY
                and item.subject_id in governed
            )
        }
        for item in district_page.items:
            merged[(item.family, item.subject_id)] = item

        ordered = sorted(merged.values(), key=lambda item: (item.family, item.subject_id))
        has_more = base_page.has_more or district_page.has_more or len(ordered) > int(limit)
        items = tuple(ordered[: int(limit)])
        last_key = (
            (items[-1].family, items[-1].subject_id)
            if has_more and items
            else None
        )
        read_model_version = max(
            [base_page.read_model_version, district_page.read_model_version]
            + [item.read_model_version for item in items]
        )
        return NationalMapPage(items, has_more, last_key, read_model_version)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized in self.city_district_repository.governed_ids():
            return self.city_district_repository.get_subject(normalized)
        return self.base_repository.get_subject(normalized)


__all__ = [
    "CITY_DISTRICT_PUBLIC_VIEW",
    "CITY_DISTRICT_FAMILY",
    "CITY_DISTRICT_CLASSIFICATION_SCHEME",
    "CITY_DISTRICT_CLASSIFICATION_CODE",
    "CITY_DISTRICT_LABEL_POINT_ALGORITHM_ID",
    "CITY_DISTRICT_LABEL_POINT_ALGORITHM_VERSION",
    "CityDistrictMapMetadata",
    "CityDistrictMapRecord",
    "PostgreSQLCityDistrictPublicMapRepository",
    "CityDistrictAugmentedNNGLANationalMapRepository",
]
