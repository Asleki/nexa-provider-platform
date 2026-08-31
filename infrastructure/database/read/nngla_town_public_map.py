"""P006.7.11.15.9.3 governed TOWN footprint augmentation for national-map reads."""
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

TOWN_PUBLIC_VIEW = "geography.nngla_town_public_read_v2"
TOWN_FAMILY = "PLACE"
TOWN_CLASSIFICATION_SCHEME = "NNGLA_PLACE_TYPE"
TOWN_CLASSIFICATION_CODE = "TOWN"
TOWN_LABEL_POINT_ALGORITHM_ID = (
    "algorithm:nngla:town-label-point-on-surface:epsg4326"
)
TOWN_LABEL_POINT_ALGORITHM_VERSION = 1


@dataclass(frozen=True, slots=True)
class TownMapMetadata:
    subject_id: str
    parent_place_id: str | None
    label_point: dict[str, object]
    area_m2: float
    perimeter_m: float
    qualification_id: str
    source_runtime_effect_scope: str
    label_point_algorithm_id: str = TOWN_LABEL_POINT_ALGORITHM_ID
    label_point_algorithm_version: int = TOWN_LABEL_POINT_ALGORITHM_VERSION
    source_view: str = TOWN_PUBLIC_VIEW

    def as_public_fields(self) -> dict[str, object]:
        return {
            "placeType": TOWN_CLASSIFICATION_CODE,
            "parentPlaceId": self.parent_place_id,
            "labelPoint": self.label_point,
            "labelAnchorKind": "DERIVED_PRESENTATION",
            "labelPointAlgorithmId": self.label_point_algorithm_id,
            "labelPointAlgorithmVersion": self.label_point_algorithm_version,
            "areaM2": self.area_m2,
            "perimeterM": self.perimeter_m,
            "qualificationId": self.qualification_id,
            "sourceRuntimeEffectScope": self.source_runtime_effect_scope,
        }


@dataclass(frozen=True, slots=True)
class TownMapRecord:
    feature: NationalMapFeature
    metadata: TownMapMetadata


class PostgreSQLTownPublicMapRepository:
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
                    SELECT place_id
                    FROM geography.nngla_place_reference
                    WHERE upper(place_type_code)='TOWN'
                    ORDER BY place_id
                    """
                )
                ids = tuple(str(row[0]) for row in cursor.fetchall())
        if not ids or len(set(ids)) != len(ids):
            raise NNGLAMapReadAuthorityError(
                "governed TOWN identity set must be non-empty and unique"
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
    ) -> tuple[TownMapRecord, ...]:
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
            SELECT v.place_id,v.parent_place_id,v.canonical_name,v.place_type_code,
                   v.publication_id,v.town_footprint_id,v.realization_version,
                   v.geometry_type_code,v.crs_code,
                   ST_AsGeoJSON(v.geometry,8)::jsonb,v.source_runtime_effect_scope,
                   jsonb_build_object(
                     'type','Point',
                     'coordinates',jsonb_build_array(v.label_longitude,v.label_latitude)
                   ),
                   v.area_m2,v.perimeter_m,v.qualification_id
            FROM {TOWN_PUBLIC_VIEW} AS v
            WHERE v.qualification_status='QUALIFIED'
              AND v.publication_status='PUBLISHED'
              {bounds_filter}
            ORDER BY v.place_id
        """
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = list(cursor.fetchall())

        governed = self.governed_ids()
        records: list[TownMapRecord] = []
        seen: set[str] = set()
        for row in rows:
            subject_id = str(row[0])
            if subject_id not in governed:
                raise NNGLAMapReadAuthorityError(
                    f"public TOWN view exposed unknown identity: {subject_id}"
                )
            if subject_id in seen:
                raise NNGLAMapReadAuthorityError(
                    f"public TOWN view returned duplicate identity: {subject_id}"
                )
            seen.add(subject_id)
            if str(row[3]).upper() != TOWN_CLASSIFICATION_CODE:
                raise NNGLAMapReadAuthorityError("TOWN public row changed place type")
            geometry = self._json_object(row[9], "TOWN geometry GeoJSON")
            label_point = self._json_object(row[11], "TOWN label point GeoJSON")
            geometry_type = str(row[7]).upper()
            expected_type = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
            if geometry.get("type") != expected_type:
                raise NNGLAMapReadAuthorityError(
                    "TOWN geometry type metadata does not match GeoJSON"
                )
            if label_point.get("type") != "Point":
                raise NNGLAMapReadAuthorityError("TOWN label point must be GeoJSON Point")
            area_m2 = float(row[12])
            perimeter_m = float(row[13])
            if area_m2 <= 0 or perimeter_m <= 0:
                raise NNGLAMapReadAuthorityError("TOWN measurements must be positive")
            runtime_scope = str(row[10]).strip()
            if not runtime_scope:
                raise NNGLAMapReadAuthorityError("TOWN runtime effect scope is required")
            parent_place_id = None if row[1] is None else str(row[1])
            feature = NationalMapFeature(
                subject_id=subject_id,
                family=TOWN_FAMILY,
                display_name=str(row[2]),
                publication_reference=str(row[4]),
                geometry_id=str(row[5]),
                geometry_version=max(1, int(row[6])),
                geometry_role="SETTLEMENT_FOOTPRINT",
                geometry_type=geometry_type,
                crs_code=str(row[8]),
                geometry=geometry,
                runtime_effect_scope=runtime_scope,
                classification_scheme=TOWN_CLASSIFICATION_SCHEME,
                classification_code=TOWN_CLASSIFICATION_CODE,
                read_model_version=1,
            )
            metadata = TownMapMetadata(
                subject_id=subject_id,
                parent_place_id=parent_place_id,
                label_point=label_point,
                area_m2=area_m2,
                perimeter_m=perimeter_m,
                qualification_id=str(row[14]),
                source_runtime_effect_scope=runtime_scope,
            )
            records.append(TownMapRecord(feature=feature, metadata=metadata))
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
        if TOWN_FAMILY not in selected:
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
    ) -> dict[str, TownMapMetadata]:
        governed = self.governed_ids()
        wanted = {str(value) for value in subject_ids if str(value) in governed}
        if not wanted:
            return {}
        return {
            record.feature.subject_id: record.metadata
            for record in self._records(bounds=None)
            if record.feature.subject_id in wanted
        }


class TownAugmentedNNGLANationalMapRepository:
    def __init__(
        self,
        base_repository: Any,
        town_repository: PostgreSQLTownPublicMapRepository,
    ) -> None:
        if base_repository is None or town_repository is None:
            raise TypeError("base_repository and town_repository are required")
        if str(base_repository.runtime_mode) != str(town_repository.runtime_mode):
            raise ValueError("base and TOWN repositories must use the same runtime_mode")
        self.base_repository = base_repository
        self.town_repository = town_repository
        self.runtime_mode = str(base_repository.runtime_mode)

    def list_features(
        self,
        *,
        bounds: MapBounds,
        families: Iterable[str] = MAP_FAMILIES,
        limit: int = 500,
        after: tuple[str, str] | None = None,
    ) -> NationalMapPage:
        governed = self.town_repository.governed_ids()
        base_page = self.base_repository.list_features(
            bounds=bounds,
            families=families,
            limit=min(2000, int(limit) + len(governed)),
            after=after,
        )
        town_page = self.town_repository.list_features(
            bounds=bounds,
            families=families,
            limit=int(limit),
            after=after,
        )

        merged: dict[tuple[str, str], NationalMapFeature] = {
            (item.family, item.subject_id): item
            for item in base_page.items
            if not (item.family == TOWN_FAMILY and item.subject_id in governed)
        }
        for item in town_page.items:
            merged[(item.family, item.subject_id)] = item

        ordered = sorted(merged.values(), key=lambda item: (item.family, item.subject_id))
        has_more = base_page.has_more or town_page.has_more or len(ordered) > int(limit)
        items = tuple(ordered[: int(limit)])
        last_key = (
            (items[-1].family, items[-1].subject_id)
            if has_more and items
            else None
        )
        read_model_version = max(
            [base_page.read_model_version, town_page.read_model_version]
            + [item.read_model_version for item in items]
        )
        return NationalMapPage(items, has_more, last_key, read_model_version)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        normalized = str(subject_id)
        if normalized in self.town_repository.governed_ids():
            return self.town_repository.get_subject(normalized)
        return self.base_repository.get_subject(normalized)


__all__ = [
    "TOWN_PUBLIC_VIEW",
    "TOWN_FAMILY",
    "TOWN_CLASSIFICATION_SCHEME",
    "TOWN_CLASSIFICATION_CODE",
    "TOWN_LABEL_POINT_ALGORITHM_ID",
    "TOWN_LABEL_POINT_ALGORITHM_VERSION",
    "TownMapMetadata",
    "TownMapRecord",
    "PostgreSQLTownPublicMapRepository",
    "TownAugmentedNNGLANationalMapRepository",
]
