"""P006.7.11.15.9.1 governed MUNICIPALITY augmentation for national-map reads.

The new MUNICIPALITY public view is sole authority for the 24 governed
MUNICIPALITY identities.  Historical generic ADMINISTRATIVE_AREA copies for
those identities are suppressed even when a municipality is unpublished.
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

MUNICIPALITY_PUBLIC_VIEW = "geography.nngla_municipality_public_read_v1"
MUNICIPALITY_FAMILY = "ADMINISTRATIVE_AREA"
MUNICIPALITY_CLASSIFICATION_SCHEME = "NNGLA_ADMIN_TYPE"
MUNICIPALITY_CLASSIFICATION_CODE = "MUNICIPALITY"
MUNICIPALITY_LABEL_POINT_ALGORITHM_ID = (
    "algorithm:nngla:municipality-label-point-on-surface:epsg4326"
)
MUNICIPALITY_LABEL_POINT_ALGORITHM_VERSION = 1
EXPECTED_MUNICIPALITY_COUNT = 24


@dataclass(frozen=True, slots=True)
class MunicipalityMapMetadata:
    subject_id: str
    parent_region_id: str
    label_point: dict[str, object]
    area_m2: float
    perimeter_m: float
    label_point_algorithm_id: str = MUNICIPALITY_LABEL_POINT_ALGORITHM_ID
    label_point_algorithm_version: int = MUNICIPALITY_LABEL_POINT_ALGORITHM_VERSION
    source_view: str = MUNICIPALITY_PUBLIC_VIEW

    def as_public_fields(self) -> dict[str, object]:
        return {
            "administrativeLevel": MUNICIPALITY_CLASSIFICATION_CODE,
            "parentRegionId": self.parent_region_id,
            "labelPoint": self.label_point,
            "labelAnchorKind": "DERIVED_PRESENTATION",
            "labelPointAlgorithmId": self.label_point_algorithm_id,
            "labelPointAlgorithmVersion": self.label_point_algorithm_version,
            "areaM2": self.area_m2,
            "perimeterM": self.perimeter_m,
        }


@dataclass(frozen=True, slots=True)
class MunicipalityMapRecord:
    feature: NationalMapFeature
    metadata: MunicipalityMapMetadata


class PostgreSQLMunicipalityPublicMapRepository:
    def __init__(self, pool: Any, *, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        normalized = str(runtime_mode).strip().lower()
        if normalized not in {"simulation", "production"}:
            raise ValueError("runtime_mode must be simulation or production")
        self.pool = pool
        self.runtime_mode = normalized

    def governed_ids(self) -> frozenset[str]:
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT administrative_area_id
                    FROM geography.nngla_administrative_area
                    WHERE administrative_type_code='MUNICIPALITY'
                    ORDER BY administrative_area_id
                    """
                )
                ids = tuple(str(row[0]) for row in cursor.fetchall())
        if len(ids) != EXPECTED_MUNICIPALITY_COUNT or len(set(ids)) != EXPECTED_MUNICIPALITY_COUNT:
            raise NNGLAMapReadAuthorityError(
                "governed MUNICIPALITY identity set must contain exactly 24 unique IDs"
            )
        return frozenset(ids)

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
    ) -> tuple[MunicipalityMapRecord, ...]:
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
            SELECT v.municipality_id,v.parent_region_id,v.canonical_name,
                   v.publication_id,1,v.municipality_geometry_id,1,
                   'ADMINISTRATIVE_BOUNDARY',v.geometry_type_code,v.crs_code,
                   ST_AsGeoJSON(v.geometry,8)::jsonb,'SHARED_REFERENCE',1,
                   jsonb_build_object(
                     'type','Point',
                     'coordinates',jsonb_build_array(v.label_longitude,v.label_latitude)
                   ),
                   v.area_m2,v.perimeter_m
            FROM {MUNICIPALITY_PUBLIC_VIEW} AS v
            WHERE v.administrative_type_code='MUNICIPALITY'
              AND v.qualification_status='QUALIFIED'
              AND v.partition_status='COMPLETE'
              AND v.publication_status='PUBLISHED'
              {bounds_filter}
            ORDER BY v.municipality_id
        """
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = list(cursor.fetchall())

        governed = self.governed_ids()
        records: list[MunicipalityMapRecord] = []
        seen: set[str] = set()
        for row in rows:
            subject_id = str(row[0])
            if subject_id not in governed:
                raise NNGLAMapReadAuthorityError(
                    f"public MUNICIPALITY view exposed unknown identity: {subject_id}"
                )
            if subject_id in seen:
                raise NNGLAMapReadAuthorityError(
                    f"public MUNICIPALITY view returned duplicate identity: {subject_id}"
                )
            seen.add(subject_id)
            parent_region_id = str(row[1])
            if not parent_region_id.startswith("NG-ADM-"):
                raise NNGLAMapReadAuthorityError("MUNICIPALITY parent REGION identity is malformed")
            geometry = self._json_object(row[10], "MUNICIPALITY geometry GeoJSON")
            label_point = self._json_object(row[13], "MUNICIPALITY label point GeoJSON")
            geometry_type = str(row[8]).upper()
            expected_type = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
            if geometry.get("type") != expected_type:
                raise NNGLAMapReadAuthorityError(
                    "MUNICIPALITY geometry type metadata does not match GeoJSON"
                )
            if label_point.get("type") != "Point":
                raise NNGLAMapReadAuthorityError("MUNICIPALITY label point must be GeoJSON Point")
            area_m2 = float(row[14])
            perimeter_m = float(row[15])
            if area_m2 <= 0 or perimeter_m <= 0:
                raise NNGLAMapReadAuthorityError("MUNICIPALITY measurements must be positive")
            feature = NationalMapFeature(
                subject_id=subject_id,
                family=MUNICIPALITY_FAMILY,
                display_name=str(row[2]),
                publication_reference=str(row[3]),
                geometry_id=str(row[5]),
                geometry_version=int(row[6]),
                geometry_role=str(row[7]),
                geometry_type=geometry_type,
                crs_code=str(row[9]),
                geometry=geometry,
                runtime_effect_scope=str(row[11]),
                classification_scheme=MUNICIPALITY_CLASSIFICATION_SCHEME,
                classification_code=MUNICIPALITY_CLASSIFICATION_CODE,
                read_model_version=max(1, int(row[12])),
            )
            metadata = MunicipalityMapMetadata(
                subject_id=subject_id,
                parent_region_id=parent_region_id,
                label_point=label_point,
                area_m2=area_m2,
                perimeter_m=perimeter_m,
            )
            records.append(MunicipalityMapRecord(feature=feature, metadata=metadata))
        return tuple(records)

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
        if MUNICIPALITY_FAMILY not in selected:
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
        for record in self._records(bounds=None):
            if record.feature.subject_id == normalized:
                return record.feature
        return None

    def metadata_for_subjects(
        self,
        subject_ids: Iterable[str],
    ) -> dict[str, MunicipalityMapMetadata]:
        governed = self.governed_ids()
        wanted = {str(value) for value in subject_ids if str(value) in governed}
        if not wanted:
            return {}
        return {
            record.feature.subject_id: record.metadata
            for record in self._records(bounds=None)
            if record.feature.subject_id in wanted
        }


class MunicipalityAugmentedNNGLANationalMapRepository:
    def __init__(self, base_repository: Any, municipality_repository: PostgreSQLMunicipalityPublicMapRepository) -> None:
        if base_repository is None or municipality_repository is None:
            raise TypeError("base_repository and municipality_repository are required")
        if str(base_repository.runtime_mode) != str(municipality_repository.runtime_mode):
            raise ValueError("base and MUNICIPALITY repositories must use the same runtime_mode")
        self.base_repository = base_repository
        self.municipality_repository = municipality_repository
        self.runtime_mode = str(base_repository.runtime_mode)

    def list_features(
        self,
        *,
        bounds: MapBounds,
        families: Iterable[str] = MAP_FAMILIES,
        limit: int = 500,
        after: tuple[str, str] | None = None,
    ) -> NationalMapPage:
        governed = self.municipality_repository.governed_ids()
        base_page = self.base_repository.list_features(
            bounds=bounds,
            families=families,
            limit=min(2000, int(limit) + EXPECTED_MUNICIPALITY_COUNT),
            after=after,
        )
        municipality_page = self.municipality_repository.list_features(
            bounds=bounds,
            families=families,
            limit=min(EXPECTED_MUNICIPALITY_COUNT, int(limit)),
            after=after,
        )

        merged: dict[tuple[str, str], NationalMapFeature] = {
            (item.family, item.subject_id): item
            for item in base_page.items
            if not (
                item.family == MUNICIPALITY_FAMILY
                and item.subject_id in governed
            )
        }
        for item in municipality_page.items:
            merged[(item.family, item.subject_id)] = item

        ordered = sorted(merged.values(), key=lambda item: (item.family, item.subject_id))
        has_more = (
            base_page.has_more
            or municipality_page.has_more
            or len(ordered) > int(limit)
        )
        items = tuple(ordered[: int(limit)])
        last_key = (
            (items[-1].family, items[-1].subject_id)
            if has_more and items
            else None
        )
        read_model_version = max(
            [base_page.read_model_version, municipality_page.read_model_version]
            + [item.read_model_version for item in items]
        )
        return NationalMapPage(items, has_more, last_key, read_model_version)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized in self.municipality_repository.governed_ids():
            return self.municipality_repository.get_subject(normalized)
        return self.base_repository.get_subject(normalized)


__all__ = [
    "EXPECTED_MUNICIPALITY_COUNT",
    "MUNICIPALITY_PUBLIC_VIEW",
    "MUNICIPALITY_FAMILY",
    "MUNICIPALITY_CLASSIFICATION_SCHEME",
    "MUNICIPALITY_CLASSIFICATION_CODE",
    "MUNICIPALITY_LABEL_POINT_ALGORITHM_ID",
    "MUNICIPALITY_LABEL_POINT_ALGORITHM_VERSION",
    "MunicipalityMapMetadata",
    "MunicipalityMapRecord",
    "PostgreSQLMunicipalityPublicMapRepository",
    "MunicipalityAugmentedNNGLANationalMapRepository",
]
