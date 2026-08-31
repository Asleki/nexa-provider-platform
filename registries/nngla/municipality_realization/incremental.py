"""Sequence-29 incremental MUNICIPALITY feature qualification/publication.

Each municipality is independently normalized to the exact current REGION
municipal domain (REGION minus current CITY), qualified, and published. Regional
fabric completeness is calculated and persisted separately.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from typing import Any

from .planning import canonical_sha256, municipality_geometry_id, partition_qualification_id
from .postgis import PostGISMunicipalityEngine
from .source import sources_for_region_source_record

PLAN_ID = "p006.7.11.15.9-seq29-municipality-feature-publication"
PLAN_VERSION = 1


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise RuntimeError(f"{label} is malformed")


def _canonical(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _effective_date(value: str | None) -> str:
    return date.fromisoformat(str(value or date.today().isoformat())).isoformat()


def _feature_qualification_id(municipality_id: str) -> str:
    return f"municipality-feature-qualification:nngla:{municipality_id}:v2"


def _feature_publication_id(municipality_id: str) -> str:
    return f"municipality-feature-publication:nngla:{municipality_id}:v2"


def _execution_id(fingerprint: str) -> str:
    return f"nnglarun:seq29-municipality:{fingerprint}"


@dataclass(frozen=True, slots=True)
class IncrementalMunicipalityPlan:
    payload: dict[str, object]

    @property
    def fingerprint(self) -> str:
        return str(self.payload["fingerprint"])

    @property
    def database_name(self) -> str:
        return str(self.payload["databaseName"])

    @property
    def confirmation_token(self) -> str:
        return (
            f"REALIZE-NNGLA-MUNICIPALITY-INCREMENTAL::"
            f"{self.database_name}::{self.fingerprint}"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            **self.payload,
            "planId": PLAN_ID,
            "planVersion": PLAN_VERSION,
            "confirmationToken": self.confirmation_token,
        }


@dataclass(frozen=True, slots=True)
class IncrementalMunicipalityExecutionResult:
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return dict(self.payload)


class IncrementalMunicipalityPublicationService:
    def __init__(
        self,
        connection: Any,
        *,
        environment_name: str,
        repository_revision: str,
        effective_date: str | None = None,
    ) -> None:
        if connection is None:
            raise TypeError("connection is required")
        if not str(environment_name).strip():
            raise ValueError("environment_name is required")
        if not str(repository_revision).strip():
            raise ValueError("repository_revision is required")
        self.connection = connection
        self.environment_name = str(environment_name).strip()
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = _effective_date(effective_date)
        self.engine = PostGISMunicipalityEngine(connection)

    @property
    def database_name(self) -> str:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("current database is unavailable")
        return str(row[0])

    def _realize(self, source, region, city) -> dict[str, object]:
        source_geojson = json.dumps(
            source.geometry,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH region AS (
                  SELECT geometry
                  FROM geography.nngla_region_geometry_record
                  WHERE region_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                ), calc AS (
                  SELECT
                    src.geometry AS source_geometry,
                    region.geometry AS region_geometry,
                    city.geometry AS city_geometry,
                    ST_CoveredBy(src.geometry,region.geometry) AS source_covered,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Difference(src.geometry,region.geometry),3
                      )::geography
                    ) AS source_outside_region_m2,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Intersection(src.geometry,city.geometry),3
                      )::geography
                    ) AS source_city_overlap_m2,
                    ST_CollectionExtract(
                      ST_Intersection(src.geometry,region.geometry),3
                    ) AS inside_region
                  FROM src CROSS JOIN region CROSS JOIN city
                ), excluded_city AS (
                  SELECT
                    source_geometry,region_geometry,city_geometry,source_covered,
                    source_outside_region_m2,source_city_overlap_m2,
                    ST_CollectionExtract(
                      ST_Difference(inside_region,city_geometry),3
                    ) AS municipality_domain_candidate
                  FROM calc
                ), final AS (
                  SELECT
                    source_geometry,region_geometry,city_geometry,source_covered,
                    source_outside_region_m2,source_city_overlap_m2,
                    ST_CollectionExtract(
                      ST_Intersection(municipality_domain_candidate,region_geometry),3
                    ) AS geometry
                  FROM excluded_city
                )
                SELECT
                  ST_IsValid(source_geometry),
                  NOT ST_IsEmpty(source_geometry),
                  ST_GeometryType(source_geometry),
                  ST_IsValid(geometry),
                  NOT ST_IsEmpty(geometry),
                  ST_GeometryType(geometry),
                  ST_CoveredBy(geometry,region_geometry),
                  ST_Area(
                    ST_CollectionExtract(
                      ST_Intersection(geometry,city_geometry),3
                    )::geography
                  ) AS final_city_overlap_m2,
                  ST_Area(source_geometry::geography),
                  source_outside_region_m2,
                  source_city_overlap_m2,
                  ST_Area(geometry::geography),
                  ST_Perimeter(geometry::geography),
                  ST_AsGeoJSON(geometry,15)::jsonb,
                  ST_AsGeoJSON(ST_PointOnSurface(geometry),15)::jsonb,
                  ST_CoveredBy(ST_PointOnSurface(geometry),geometry),
                  source_covered
                FROM final
                """,
                (
                    region.region_geometry_id,
                    region.region_id,
                    region.geometry_sha256,
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    source_geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("exact current REGION/CITY authority is unavailable")
        source_type = str(row[2]).removeprefix("ST_").upper()
        final_type = str(row[5]).removeprefix("ST_").upper()
        if not bool(row[0]) or not bool(row[1]) or source_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise RuntimeError("SOURCE_INVALID_OR_NON_POLYGONAL")
        if not bool(row[3]) or not bool(row[4]) or final_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise RuntimeError("NORMALIZED_GEOMETRY_INVALID_OR_EMPTY")
        if not bool(row[6]):
            raise RuntimeError("PARENT_REGION_CONTAINMENT_FAILED")
        if float(row[7]) != 0.0:
            raise RuntimeError("CITY_POSITIVE_AREA_CONFLICT")
        if not bool(row[15]):
            raise RuntimeError("LABEL_POINT_INVALID")
        area_m2 = float(row[11])
        perimeter_m = float(row[12])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise RuntimeError("NON_POSITIVE_MEASUREMENT")
        geometry = _json_object(row[13], "MUNICIPALITY geometry")
        label_point = _json_object(row[14], "MUNICIPALITY label point")
        source_covered = bool(row[16])
        source_city_overlap = max(0.0, float(row[10]))
        return {
            "municipalityId": source.administrative_area_id,
            "canonicalName": source.canonical_name,
            "regionCode": source.region_code,
            "sourceRecordId": source.source_record_id,
            "sourceDatasetId": source.source_dataset_id,
            "sourceDatasetVersion": source.source_dataset_version,
            "sourcePathReference": source.source_path_reference,
            "sourceDatasetSha256": source.source_dataset_sha256,
            "sourceGeometrySha256": source.source_geometry_sha256,
            "geometryId": municipality_geometry_id(source.administrative_area_id),
            "featureQualificationId": _feature_qualification_id(source.administrative_area_id),
            "publicationId": _feature_publication_id(source.administrative_area_id),
            "realizationMethod": (
                "SOURCE_REUSE"
                if source_covered and source_city_overlap == 0.0
                else "REGION_CITY_CONTAINED_NORMALIZATION"
            ),
            "geometryTypeCode": final_type,
            "geometry": geometry,
            "geometrySha256": canonical_sha256(geometry),
            "labelPoint": label_point,
            "sourceAreaM2": float(row[8]),
            "sourceOutsideRegionM2": max(0.0, float(row[9])),
            "sourceCityOverlapM2": source_city_overlap,
            "cityPositiveOverlapM2": max(0.0, float(row[7])),
            "areaM2": area_m2,
            "areaKm2": area_m2 / 1_000_000.0,
            "perimeterM": perimeter_m,
            "perimeterKm": perimeter_m / 1000.0,
        }

    def _sibling_overlap(self, realized: list[dict[str, object]]) -> dict[str, float]:
        if not realized:
            return {}
        payload = json.dumps(
            [
                {"municipalityId": item["municipalityId"], "geometry": item["geometry"]}
                for item in realized
            ],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH src AS (
                  SELECT
                    value->>'municipalityId' AS municipality_id,
                    ST_SetSRID(ST_GeomFromGeoJSON((value->'geometry')::text),4326) AS geometry
                  FROM jsonb_array_elements(%s::jsonb)
                ), pairs AS (
                  SELECT
                    a.municipality_id AS a_id,
                    b.municipality_id AS b_id,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Intersection(a.geometry,b.geometry),3
                      )::geography
                    ) AS overlap_m2
                  FROM src a JOIN src b ON a.municipality_id < b.municipality_id
                ), expanded AS (
                  SELECT a_id AS municipality_id,overlap_m2 FROM pairs
                  UNION ALL
                  SELECT b_id AS municipality_id,overlap_m2 FROM pairs
                )
                SELECT s.municipality_id,COALESCE(sum(e.overlap_m2),0.0)
                FROM src s LEFT JOIN expanded e USING (municipality_id)
                GROUP BY s.municipality_id ORDER BY s.municipality_id
                """,
                (payload,),
            )
            return {str(row[0]): max(0.0, float(row[1])) for row in cursor.fetchall()}

    def _fabric(self, region, city, realized: list[dict[str, object]]) -> dict[str, object]:
        payload = json.dumps(
            [item["geometry"] for item in realized],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH region AS (
                  SELECT geometry
                  FROM geography.nngla_region_geometry_record
                  WHERE region_geometry_id=%s AND administrative_area_id=%s
                    AND geometry_sha256=%s AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s AND administrative_area_id=%s
                    AND geometry_sha256=%s AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT row_number() OVER () AS ordinal,
                         ST_SetSRID(ST_GeomFromGeoJSON(value::text),4326) AS geometry
                  FROM jsonb_array_elements(%s::jsonb)
                ), agg AS (
                  SELECT count(*)::integer AS observed_count,
                         COALESCE(bool_and(ST_IsValid(src.geometry)),true) AS all_valid,
                         COALESCE(bool_and(NOT ST_IsEmpty(src.geometry)),true) AS all_non_empty,
                         COALESCE(bool_and(ST_GeometryType(src.geometry) IN ('ST_Polygon','ST_MultiPolygon')),true) AS all_polygonal,
                         COALESCE(bool_and(ST_CoveredBy(src.geometry,region.geometry)),true) AS all_covered_by_region,
                         ST_UnaryUnion(ST_Collect(src.geometry)) AS municipality_union
                  FROM src CROSS JOIN region
                ), sibling AS (
                  SELECT COALESCE(sum(
                    ST_Area(ST_CollectionExtract(ST_Intersection(a.geometry,b.geometry),3)::geography)
                  ),0.0) AS sibling_overlap_m2
                  FROM src a JOIN src b ON a.ordinal < b.ordinal
                ), city_overlap AS (
                  SELECT COALESCE(sum(
                    ST_Area(ST_CollectionExtract(ST_Intersection(src.geometry,city.geometry),3)::geography)
                  ),0.0) AS city_overlap_m2
                  FROM src CROSS JOIN city
                ), combined AS (
                  SELECT CASE
                    WHEN agg.municipality_union IS NULL THEN city.geometry
                    ELSE ST_UnaryUnion(ST_Collect(city.geometry,agg.municipality_union))
                  END AS union_geometry,
                  agg.observed_count,agg.all_valid,agg.all_non_empty,agg.all_polygonal,
                  agg.all_covered_by_region,sibling.sibling_overlap_m2,city_overlap.city_overlap_m2
                  FROM agg CROSS JOIN sibling CROSS JOIN city_overlap CROSS JOIN city
                )
                SELECT
                  combined.observed_count,combined.all_valid,combined.all_non_empty,
                  combined.all_polygonal,combined.all_covered_by_region,
                  ST_CoveredBy(city.geometry,region.geometry),
                  combined.sibling_overlap_m2,combined.city_overlap_m2,
                  ST_Equals(combined.union_geometry,region.geometry),
                  ST_Area(combined.union_geometry::geography),
                  ST_Area(region.geometry::geography),
                  ST_Area(ST_CollectionExtract(
                    ST_SymDifference(combined.union_geometry,region.geometry),3
                  )::geography)
                FROM combined CROSS JOIN city CROSS JOIN region
                """,
                (
                    region.region_geometry_id, region.region_id, region.geometry_sha256,
                    city.city_geometry_id, city.city_id, city.geometry_sha256,
                    payload,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("MUNICIPALITY fabric proof is unavailable")
        evidence = {
            "expected_count": 3,
            "observed_count": int(row[0]),
            "all_valid": bool(row[1]),
            "all_non_empty": bool(row[2]),
            "all_polygonal": bool(row[3]),
            "all_covered_by_region": bool(row[4]),
            "city_covered_by_region": bool(row[5]),
            "municipality_sibling_positive_overlap_m2": max(0.0, float(row[6])),
            "city_municipality_positive_overlap_m2": max(0.0, float(row[7])),
            "union_equals_region": bool(row[8]),
            "union_area_m2": float(row[9]),
            "region_area_m2": float(row[10]),
            "symmetric_difference_m2": max(0.0, float(row[11])),
        }
        evidence["fabric_status"] = (
            "COMPLETE"
            if evidence["observed_count"] == 3
            and evidence["all_valid"]
            and evidence["all_non_empty"]
            and evidence["all_polygonal"]
            and evidence["all_covered_by_region"]
            and evidence["city_covered_by_region"]
            and evidence["municipality_sibling_positive_overlap_m2"] == 0.0
            and evidence["city_municipality_positive_overlap_m2"] == 0.0
            and evidence["union_equals_region"]
            else "PARTIAL"
        )
        return evidence

    def preview_region(self, region_id: str) -> IncrementalMunicipalityPlan:
        region = self.engine.load_region(str(region_id).strip())
        city = self.engine.load_city(region.region_id)
        sources = sources_for_region_source_record(region.source_record_id)
        realized: list[dict[str, object]] = []
        rejected: list[dict[str, object]] = []

        for source in sources:
            try:
                identity = self.engine.load_identity(source.administrative_area_id)
                identity_match = (
                    identity.canonical_name,
                    identity.region_code,
                    identity.source_record_id,
                    identity.parent_source_record_id,
                ) == (
                    source.canonical_name,
                    source.region_code,
                    source.source_record_id,
                    source.parent_source_record_id,
                )
                if not identity_match:
                    raise RuntimeError("IDENTITY_SOURCE_CONTRACT_MISMATCH")
                if identity.parent_source_record_id != region.source_record_id:
                    raise RuntimeError("PARENT_REGION_BINDING_MISMATCH")
                item = self._realize(source, region, city)
                item["identityParentageMatch"] = True
                item["sourceContractMatch"] = True
                realized.append(item)
            except Exception as exc:
                rejected.append(
                    {
                        "municipalityId": source.administrative_area_id,
                        "canonicalName": source.canonical_name,
                        "sourceRecordId": source.source_record_id,
                        "sourceDatasetSha256": source.source_dataset_sha256,
                        "sourceGeometrySha256": source.source_geometry_sha256,
                        "qualificationStatus": "REJECTED",
                        "rejectionCode": str(exc),
                    }
                )

        overlaps = self._sibling_overlap(realized)
        candidates: list[dict[str, object]] = []
        for item in realized:
            item = dict(item)
            overlap = overlaps.get(str(item["municipalityId"]), 0.0)
            item["municipalitySiblingPositiveOverlapM2"] = overlap
            if overlap == 0.0 and float(item["cityPositiveOverlapM2"]) == 0.0:
                item["qualificationStatus"] = "QUALIFIED"
                item["rejectionCode"] = None
            else:
                item["qualificationStatus"] = "REJECTED"
                item["rejectionCode"] = (
                    "MUNICIPALITY_SIBLING_POSITIVE_AREA_CONFLICT"
                    if overlap != 0.0
                    else "CITY_POSITIVE_AREA_CONFLICT"
                )
            item["featureFingerprint"] = _canonical(
                {
                    "planId": PLAN_ID,
                    "municipalityId": item["municipalityId"],
                    "parentRegionId": region.region_id,
                    "parentRegionGeometryId": region.region_geometry_id,
                    "parentRegionGeometrySha256": region.geometry_sha256,
                    "cityId": city.city_id,
                    "cityGeometryId": city.city_geometry_id,
                    "cityGeometrySha256": city.geometry_sha256,
                    "sourceGeometrySha256": item["sourceGeometrySha256"],
                    "geometrySha256": item["geometrySha256"],
                    "cityPositiveOverlapM2": item["cityPositiveOverlapM2"],
                    "municipalitySiblingPositiveOverlapM2": overlap,
                    "qualificationStatus": item["qualificationStatus"],
                }
            )
            candidates.append(item)

        for item in rejected:
            item["featureFingerprint"] = _canonical(
                {
                    "planId": PLAN_ID,
                    "municipalityId": item["municipalityId"],
                    "parentRegionId": region.region_id,
                    "parentRegionGeometryId": region.region_geometry_id,
                    "parentRegionGeometrySha256": region.geometry_sha256,
                    "cityId": city.city_id,
                    "cityGeometryId": city.city_geometry_id,
                    "cityGeometrySha256": city.geometry_sha256,
                    "sourceGeometrySha256": item["sourceGeometrySha256"],
                    "qualificationStatus": "REJECTED",
                    "rejectionCode": item["rejectionCode"],
                }
            )
            candidates.append(item)

        candidates.sort(key=lambda item: str(item["municipalityId"]))
        fabric = self._fabric(region, city, realized)
        member_set = tuple(
            sorted(
                (
                    {
                        "municipalityId": str(item["municipalityId"]),
                        "geometryId": str(item["geometryId"]),
                        "geometrySha256": str(item["geometrySha256"]),
                    }
                    for item in realized
                ),
                key=lambda row: row["municipalityId"],
            )
        )
        member_sha = _canonical(member_set)
        body = {
            "databaseName": self.database_name,
            "environmentName": self.environment_name,
            "repositoryRevision": self.repository_revision,
            "effectiveDate": self.effective_date,
            "parentRegionId": region.region_id,
            "parentRegionName": region.canonical_name,
            "regionCode": region.region_code,
            "parentRegionGeometryId": region.region_geometry_id,
            "parentRegionGeometrySha256": region.geometry_sha256,
            "cityId": city.city_id,
            "cityGeometryId": city.city_geometry_id,
            "cityGeometrySha256": city.geometry_sha256,
            "cityPublicationId": city.publication_id,
            "partitionQualificationId": partition_qualification_id(region.region_id),
            "municipalityGeometrySetSha256": member_sha,
            "municipalityMemberSet": member_set,
            "municipalities": tuple(candidates),
            "fabric": fabric,
        }
        body["fingerprint"] = _canonical({"planId": PLAN_ID, "planVersion": PLAN_VERSION, **body})
        return IncrementalMunicipalityPlan(body)

    def _receipt_exists(self, fingerprint: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM geography.nngla_execution_receipt
                WHERE fingerprint_sha256=%s
                  AND database_name=current_database()
                  AND environment_name=%s
                """,
                (fingerprint, self.environment_name),
            )
            return cursor.fetchone() is not None

    def _feature_public_exists(self, item: dict[str, object]) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM geography.nngla_municipality_feature_publication
                WHERE administrative_area_id=%s
                  AND publication_id=%s
                  AND publication_status='PUBLISHED'
                """,
                (item["municipalityId"], item["publicationId"]),
            )
            return cursor.fetchone() is not None

    def _write_receipt(self, item, *, submitter, approver, status, inserted, reused, failed, publication_ready, detail):
        now = datetime.now(timezone.utc)
        fingerprint = str(item["featureFingerprint"])
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_receipt(
                  execution_id,plan_id,plan_version,fingerprint_sha256,database_name,
                  environment_name,runtime_mode,repository_revision,source_sha256,
                  submitter_actor_id,approver_actor_id,selected_count,inserted_count,
                  reused_count,quarantined_count,failed_count,status,started_at,completed_at
                ) VALUES (
                  %s,%s,%s,%s,current_database(),%s,'production',%s,%s,%s,%s,
                  1,%s,%s,0,%s,%s,%s,%s
                )
                """,
                (
                    _execution_id(fingerprint), PLAN_ID, PLAN_VERSION, fingerprint,
                    self.environment_name, self.repository_revision, item["sourceDatasetSha256"],
                    submitter, approver, inserted, reused, failed, status, now, now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_item(
                  execution_id,source_record_id,canonical_id,outcome,publication_ready,detail
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    _execution_id(fingerprint), item["sourceRecordId"], item["municipalityId"],
                    status, publication_ready,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )

    def _persist_qualified(self, plan: IncrementalMunicipalityPlan, item: dict[str, object], submitter: str, approver: str) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            if not self._feature_public_exists(item):
                raise RuntimeError("MUNICIPALITY execution receipt exists but public feature is absent")
            return "REUSED"
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT municipality_geometry_id,geometry_sha256
                FROM geography.nngla_municipality_geometry_record
                WHERE administrative_area_id=%s
                  AND effective_to IS NULL
                  AND qualification_status='QUALIFIED'
                """,
                (item["municipalityId"],),
            )
            current = cursor.fetchone()
            geometry_inserted = False
            if current is None:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_municipality_geometry_record(
                      municipality_geometry_id,administrative_area_id,parent_region_id,
                      parent_region_geometry_id,parent_region_geometry_sha256,canonical_name,
                      source_record_id,source_dataset_id,source_dataset_version,source_path_reference,
                      source_dataset_sha256,source_geometry_sha256,realization_method,realization_version,
                      geometry_type_code,crs_code,geometry,area_m2,area_km2,perimeter_m,perimeter_km,
                      label_point,geometry_sha256,qualification_status,effective_from
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,'NG-CRS-EPSG4326',
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,%s,%s,%s,
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,'QUALIFIED',%s
                    )
                    """,
                    (
                        item["geometryId"], item["municipalityId"], plan.payload["parentRegionId"],
                        plan.payload["parentRegionGeometryId"], plan.payload["parentRegionGeometrySha256"],
                        item["canonicalName"], item["sourceRecordId"], item["sourceDatasetId"],
                        item["sourceDatasetVersion"], item["sourcePathReference"], item["sourceDatasetSha256"],
                        item["sourceGeometrySha256"], item["realizationMethod"], item["geometryTypeCode"],
                        json.dumps(item["geometry"], separators=(",", ":"), ensure_ascii=False),
                        item["areaM2"], item["areaKm2"], item["perimeterM"], item["perimeterKm"],
                        json.dumps(item["labelPoint"], separators=(",", ":"), ensure_ascii=False),
                        item["geometrySha256"], self.effective_date,
                    ),
                )
                geometry_inserted = True
            elif (str(current[0]), str(current[1])) != (str(item["geometryId"]), str(item["geometrySha256"])):
                raise RuntimeError("current MUNICIPALITY geometry differs from approved feature plan")

            cursor.execute(
                """
                INSERT INTO geography.nngla_municipality_feature_qualification(
                  feature_qualification_id,administrative_area_id,municipality_geometry_id,geometry_sha256,
                  source_geometry_sha256,parent_region_id,parent_region_geometry_id,parent_region_geometry_sha256,
                  city_id,city_geometry_id,city_geometry_sha256,identity_parentage_match,source_contract_match,
                  is_valid,is_non_empty,is_polygonal,covered_by_parent_region,city_positive_overlap_m2,
                  municipality_sibling_positive_overlap_m2,feature_fingerprint_sha256,
                  qualification_status,rejection_code,policy_version,qualified_at
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,true,true,true,true,true,%s,%s,%s,
                  'QUALIFIED',NULL,2,%s
                ) ON CONFLICT (feature_qualification_id) DO NOTHING
                """,
                (
                    item["featureQualificationId"], item["municipalityId"], item["geometryId"],
                    item["geometrySha256"], item["sourceGeometrySha256"], plan.payload["parentRegionId"],
                    plan.payload["parentRegionGeometryId"], plan.payload["parentRegionGeometrySha256"],
                    plan.payload["cityId"], plan.payload["cityGeometryId"], plan.payload["cityGeometrySha256"],
                    item["cityPositiveOverlapM2"], item["municipalitySiblingPositiveOverlapM2"],
                    item["featureFingerprint"], datetime.now(timezone.utc),
                ),
            )
            cursor.execute(
                """
                SELECT publication_id
                FROM geography.nngla_municipality_feature_publication
                WHERE administrative_area_id=%s AND publication_status='PUBLISHED'
                """,
                (item["municipalityId"],),
            )
            existing_pub = cursor.fetchone()
            publication_inserted = False
            if existing_pub is None:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_municipality_feature_publication(
                      publication_id,administrative_area_id,municipality_geometry_id,
                      feature_qualification_id,publication_status,published_at
                    ) VALUES (%s,%s,%s,%s,'PUBLISHED',%s)
                    """,
                    (
                        item["publicationId"], item["municipalityId"], item["geometryId"],
                        item["featureQualificationId"], datetime.now(timezone.utc),
                    ),
                )
                publication_inserted = True
            elif str(existing_pub[0]) != str(item["publicationId"]):
                raise RuntimeError("current MUNICIPALITY feature publication differs from approved plan")

        applied = geometry_inserted or publication_inserted
        self._write_receipt(
            item, submitter=submitter, approver=approver,
            status="APPLIED" if applied else "REUSED",
            inserted=1 if applied else 0, reused=0 if applied else 1, failed=0,
            publication_ready=True,
            detail={
                "parent_region_id": plan.payload["parentRegionId"],
                "municipality_id": item["municipalityId"],
                "municipality_geometry_id": item["geometryId"],
                "feature_qualification_id": item["featureQualificationId"],
                "publication_id": item["publicationId"],
                "geometry_sha256": item["geometrySha256"],
                "fabric_status": plan.payload["fabric"]["fabric_status"],
            },
        )
        return "APPLIED" if applied else "REUSED"

    def _persist_rejected(self, plan, item, submitter, approver) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            return "REUSED"
        self._write_receipt(
            item, submitter=submitter, approver=approver, status="FAILED",
            inserted=0, reused=0, failed=1, publication_ready=False,
            detail={
                "parent_region_id": plan.payload["parentRegionId"],
                "municipality_id": item["municipalityId"],
                "rejection_code": item.get("rejectionCode"),
                "source_geometry_sha256": item["sourceGeometrySha256"],
                "fabric_status": plan.payload["fabric"]["fabric_status"],
            },
        )
        return "FAILED"

    def _persist_fabric(self, plan: IncrementalMunicipalityPlan) -> None:
        fabric = dict(plan.payload["fabric"])
        partition_status = "COMPLETE" if fabric["fabric_status"] == "COMPLETE" else "INCOMPLETE"
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_municipality_partition_qualification(
                  partition_qualification_id,parent_region_id,parent_region_geometry_id,
                  parent_region_geometry_sha256,city_id,city_geometry_id,city_geometry_sha256,
                  city_publication_id,expected_municipality_count,observed_municipality_count,
                  municipality_geometry_set_sha256,municipality_member_set,
                  all_valid,all_non_empty,all_polygonal,all_covered_by_region,city_covered_by_region,
                  municipality_sibling_positive_overlap_m2,city_municipality_positive_overlap_m2,
                  union_equals_region,union_area_m2,region_area_m2,symmetric_difference_m2,
                  partition_status,qualification_policy_version,effective_from
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,3,%s,%s,%s::jsonb,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s
                )
                ON CONFLICT (partition_qualification_id) DO UPDATE SET
                  observed_municipality_count=EXCLUDED.observed_municipality_count,
                  municipality_geometry_set_sha256=EXCLUDED.municipality_geometry_set_sha256,
                  municipality_member_set=EXCLUDED.municipality_member_set,
                  all_valid=EXCLUDED.all_valid,
                  all_non_empty=EXCLUDED.all_non_empty,
                  all_polygonal=EXCLUDED.all_polygonal,
                  all_covered_by_region=EXCLUDED.all_covered_by_region,
                  city_covered_by_region=EXCLUDED.city_covered_by_region,
                  municipality_sibling_positive_overlap_m2=EXCLUDED.municipality_sibling_positive_overlap_m2,
                  city_municipality_positive_overlap_m2=EXCLUDED.city_municipality_positive_overlap_m2,
                  union_equals_region=EXCLUDED.union_equals_region,
                  union_area_m2=EXCLUDED.union_area_m2,
                  region_area_m2=EXCLUDED.region_area_m2,
                  symmetric_difference_m2=EXCLUDED.symmetric_difference_m2,
                  partition_status=EXCLUDED.partition_status,
                  effective_from=EXCLUDED.effective_from,
                  effective_to=NULL
                """,
                (
                    plan.payload["partitionQualificationId"], plan.payload["parentRegionId"],
                    plan.payload["parentRegionGeometryId"], plan.payload["parentRegionGeometrySha256"],
                    plan.payload["cityId"], plan.payload["cityGeometryId"], plan.payload["cityGeometrySha256"],
                    plan.payload["cityPublicationId"], fabric["observed_count"],
                    plan.payload["municipalityGeometrySetSha256"],
                    json.dumps(plan.payload["municipalityMemberSet"], sort_keys=True, separators=(",", ":")),
                    fabric["all_valid"], fabric["all_non_empty"], fabric["all_polygonal"],
                    fabric["all_covered_by_region"], fabric["city_covered_by_region"],
                    fabric["municipality_sibling_positive_overlap_m2"],
                    fabric["city_municipality_positive_overlap_m2"], fabric["union_equals_region"],
                    fabric["union_area_m2"], fabric["region_area_m2"], fabric["symmetric_difference_m2"],
                    partition_status, self.effective_date,
                ),
            )

    def execute_region(
        self,
        region_id: str,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ) -> IncrementalMunicipalityExecutionResult:
        submitter = str(submitter_actor_id).strip()
        approver = str(approver_actor_id).strip()
        if not submitter or not approver:
            raise ValueError("submitter and approver actor IDs are required")
        if submitter == approver:
            raise ValueError("submitter and approver must be different actors")

        plan = self.preview_region(region_id)
        if plan.fingerprint != str(approved_fingerprint).strip():
            raise RuntimeError("approved fingerprint does not match fresh MUNICIPALITY incremental plan")
        if plan.confirmation_token != str(confirmation).strip():
            raise RuntimeError("confirmation token does not match fresh MUNICIPALITY incremental plan")
        self.connection.commit()

        inserted = reused = failed = 0
        outcomes: list[dict[str, object]] = []
        for item in plan.payload["municipalities"]:
            try:
                with self.connection.transaction():
                    if item["qualificationStatus"] == "QUALIFIED":
                        outcome = self._persist_qualified(plan, item, submitter, approver)
                        if outcome == "APPLIED": inserted += 1
                        else: reused += 1
                    else:
                        outcome = self._persist_rejected(plan, item, submitter, approver)
                        if outcome == "FAILED": failed += 1
                        else: reused += 1
                outcomes.append({"municipalityId": item["municipalityId"], "outcome": outcome})
            except Exception as exc:
                failed += 1
                receipt_error = None
                failure_item = dict(item)
                failure_item["featureFingerprint"] = _canonical({
                    "approvedFeatureFingerprint": item["featureFingerprint"],
                    "runtimeFailure": str(exc),
                })
                try:
                    with self.connection.transaction():
                        self._write_receipt(
                            failure_item, submitter=submitter, approver=approver,
                            status="FAILED", inserted=0, reused=0, failed=1,
                            publication_ready=False,
                            detail={
                                "parent_region_id": plan.payload["parentRegionId"],
                                "municipality_id": item["municipalityId"],
                                "rejection_code": "PERSISTENCE_ERROR",
                                "error": str(exc),
                                "approved_feature_fingerprint": item["featureFingerprint"],
                            },
                        )
                except Exception as receipt_exc:
                    receipt_error = str(receipt_exc)
                outcome = {"municipalityId": item["municipalityId"], "outcome": "FAILED", "error": str(exc)}
                if receipt_error:
                    outcome["receiptError"] = receipt_error
                outcomes.append(outcome)

        with self.connection.transaction():
            self._persist_fabric(plan)

        return IncrementalMunicipalityExecutionResult(
            {
                "planId": PLAN_ID,
                "planVersion": PLAN_VERSION,
                "fingerprint": plan.fingerprint,
                "parentRegionId": plan.payload["parentRegionId"],
                "databaseName": plan.database_name,
                "environmentName": self.environment_name,
                "repositoryRevision": self.repository_revision,
                "status": (
                    "PARTIAL" if failed and (inserted or reused)
                    else "FAILED" if failed
                    else "APPLIED" if inserted
                    else "REUSED"
                ),
                "insertedCount": inserted,
                "reusedCount": reused,
                "failedCount": failed,
                "fabricStatus": plan.payload["fabric"]["fabric_status"],
                "outcomes": outcomes,
            }
        )
