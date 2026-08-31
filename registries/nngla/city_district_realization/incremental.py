"""Sequence-29 incremental CITY_DISTRICT feature qualification/publication.

A district is qualified and published independently against its exact current
published CITY. City-wide fabric completeness is calculated separately and is
never used as an individual publication gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .planning import canonical_sha256, district_geometry_id, partition_qualification_id
from .postgis import PostGISCityDistrictEngine
from .source import sources_for_city_source_record

PLAN_ID = "p006.7.11.15.9-seq29-city-district-feature-publication"
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


def _feature_qualification_id(district_id: str) -> str:
    return f"city-district-feature-qualification:nngla:{district_id}:v2"


def _feature_publication_id(district_id: str) -> str:
    return f"city-district-feature-publication:nngla:{district_id}:v2"


def _execution_id(fingerprint: str) -> str:
    return f"nnglarun:seq29-city-district:{fingerprint}"


@dataclass(frozen=True, slots=True)
class IncrementalCityDistrictPlan:
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
            f"REALIZE-NNGLA-CITY-DISTRICT-INCREMENTAL::"
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
class IncrementalCityDistrictExecutionResult:
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return dict(self.payload)


class IncrementalCityDistrictPublicationService:
    def __init__(
        self,
        connection: Any,
        *,
        source_path: Path,
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
        self.source_path = Path(source_path)
        self.environment_name = str(environment_name).strip()
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = _effective_date(effective_date)
        self.engine = PostGISCityDistrictEngine(connection)

    @property
    def database_name(self) -> str:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("current database is unavailable")
        return str(row[0])

    def _realize(self, source, city) -> dict[str, object]:
        source_geojson = json.dumps(
            source.geometry,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH city AS (
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
                    city.geometry AS city_geometry,
                    ST_CoveredBy(src.geometry,city.geometry) AS source_covered,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Difference(src.geometry,city.geometry),3
                      )::geography
                    ) AS source_outside_city_m2,
                    CASE
                      WHEN ST_CoveredBy(src.geometry,city.geometry)
                      THEN src.geometry
                      ELSE ST_CollectionExtract(
                        ST_Intersection(src.geometry,city.geometry),3
                      )
                    END AS candidate_geometry
                  FROM src CROSS JOIN city
                ), final AS (
                  SELECT
                    source_geometry,
                    city_geometry,
                    source_covered,
                    source_outside_city_m2,
                    ST_CollectionExtract(
                      ST_Intersection(candidate_geometry,city_geometry),3
                    ) AS geometry
                  FROM calc
                )
                SELECT
                  ST_IsValid(source_geometry),
                  NOT ST_IsEmpty(source_geometry),
                  ST_GeometryType(source_geometry),
                  ST_IsValid(geometry),
                  NOT ST_IsEmpty(geometry),
                  ST_GeometryType(geometry),
                  ST_CoveredBy(geometry,city_geometry),
                  ST_Area(geometry::geography),
                  ST_Perimeter(geometry::geography),
                  ST_AsGeoJSON(geometry,15)::jsonb,
                  ST_AsGeoJSON(ST_PointOnSurface(geometry),15)::jsonb,
                  ST_CoveredBy(ST_PointOnSurface(geometry),geometry),
                  source_covered,
                  source_outside_city_m2
                FROM final
                """,
                (
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    source_geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("exact current CITY geometry is unavailable")
        source_type = str(row[2]).removeprefix("ST_").upper()
        final_type = str(row[5]).removeprefix("ST_").upper()
        if not bool(row[0]) or not bool(row[1]) or source_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise RuntimeError("SOURCE_INVALID_OR_NON_POLYGONAL")
        if not bool(row[3]) or not bool(row[4]) or final_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise RuntimeError("NORMALIZED_GEOMETRY_INVALID_OR_EMPTY")
        if not bool(row[6]):
            raise RuntimeError("PARENT_CONTAINMENT_FAILED")
        if not bool(row[11]):
            raise RuntimeError("LABEL_POINT_INVALID")
        area_m2 = float(row[7])
        perimeter_m = float(row[8])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise RuntimeError("NON_POSITIVE_MEASUREMENT")
        geometry = _json_object(row[9], "CITY_DISTRICT geometry")
        label_point = _json_object(row[10], "CITY_DISTRICT label point")
        return {
            "districtId": source.administrative_area_id,
            "canonicalName": source.canonical_name,
            "regionCode": source.region_code,
            "sourceRecordId": source.source_record_id,
            "parentSourceRecordId": source.parent_source_record_id,
            "sourceDatasetId": source.source_dataset_id,
            "sourceDatasetVersion": source.source_dataset_version,
            "sourcePathReference": source.source_path_reference,
            "sourceDatasetSha256": source.source_dataset_sha256,
            "sourceGeometrySha256": source.source_geometry_sha256,
            "geometryId": district_geometry_id(source.administrative_area_id),
            "featureQualificationId": _feature_qualification_id(source.administrative_area_id),
            "publicationId": _feature_publication_id(source.administrative_area_id),
            "realizationMethod": "SOURCE_REUSE" if bool(row[12]) else "CITY_PARTITION_NORMALIZATION",
            "geometryTypeCode": final_type,
            "geometry": geometry,
            "geometrySha256": canonical_sha256(geometry),
            "labelPoint": label_point,
            "areaM2": area_m2,
            "areaKm2": area_m2 / 1_000_000.0,
            "perimeterM": perimeter_m,
            "perimeterKm": perimeter_m / 1000.0,
            "sourceOutsideCityM2": max(0.0, float(row[13])),
        }

    def _sibling_overlap(self, realized: list[dict[str, object]]) -> dict[str, float]:
        if not realized:
            return {}
        payload = json.dumps(
            [
                {"districtId": item["districtId"], "geometry": item["geometry"]}
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
                    value->>'districtId' AS district_id,
                    ST_SetSRID(ST_GeomFromGeoJSON((value->'geometry')::text),4326) AS geometry
                  FROM jsonb_array_elements(%s::jsonb)
                ), pairs AS (
                  SELECT
                    a.district_id AS a_id,
                    b.district_id AS b_id,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Intersection(a.geometry,b.geometry),3
                      )::geography
                    ) AS overlap_m2
                  FROM src AS a
                  JOIN src AS b ON a.district_id < b.district_id
                ), expanded AS (
                  SELECT a_id AS district_id, overlap_m2 FROM pairs
                  UNION ALL
                  SELECT b_id AS district_id, overlap_m2 FROM pairs
                )
                SELECT s.district_id,COALESCE(sum(e.overlap_m2),0.0)
                FROM src AS s
                LEFT JOIN expanded AS e USING (district_id)
                GROUP BY s.district_id
                ORDER BY s.district_id
                """,
                (payload,),
            )
            return {str(row[0]): max(0.0, float(row[1])) for row in cursor.fetchall()}

    def _fabric(self, city, realized: list[dict[str, object]]) -> dict[str, object]:
        payload = json.dumps(
            [item["geometry"] for item in realized],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT row_number() OVER () AS ordinal,
                         ST_SetSRID(ST_GeomFromGeoJSON(value::text),4326) AS geometry
                  FROM jsonb_array_elements(%s::jsonb)
                ), aggregate AS (
                  SELECT count(*)::integer AS observed_count,
                         COALESCE(bool_and(ST_IsValid(geometry)),true) AS all_valid,
                         COALESCE(bool_and(NOT ST_IsEmpty(geometry)),true) AS all_non_empty,
                         COALESCE(bool_and(ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')),true) AS all_polygonal,
                         COALESCE(bool_and(ST_CoveredBy(geometry,city.geometry)),true) AS all_covered_by_city,
                         ST_UnaryUnion(ST_Collect(geometry)) AS district_union
                  FROM src CROSS JOIN city
                ), overlap AS (
                  SELECT COALESCE(sum(
                    ST_Area(ST_CollectionExtract(ST_Intersection(a.geometry,b.geometry),3)::geography)
                  ),0.0) AS sibling_overlap_m2
                  FROM src a JOIN src b ON a.ordinal < b.ordinal
                )
                SELECT
                  aggregate.observed_count,aggregate.all_valid,aggregate.all_non_empty,
                  aggregate.all_polygonal,aggregate.all_covered_by_city,overlap.sibling_overlap_m2,
                  CASE WHEN aggregate.district_union IS NULL THEN false
                       ELSE ST_Equals(aggregate.district_union,city.geometry) END,
                  COALESCE(ST_Area(aggregate.district_union::geography),0.0),
                  ST_Area(city.geometry::geography),
                  CASE WHEN aggregate.district_union IS NULL THEN ST_Area(city.geometry::geography)
                       ELSE ST_Area(ST_CollectionExtract(
                         ST_SymDifference(aggregate.district_union,city.geometry),3
                       )::geography) END
                FROM aggregate CROSS JOIN overlap CROSS JOIN city
                """,
                (
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    payload,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("CITY_DISTRICT fabric proof is unavailable")
        evidence = {
            "expected_count": 8,
            "observed_count": int(row[0]),
            "all_valid": bool(row[1]),
            "all_non_empty": bool(row[2]),
            "all_polygonal": bool(row[3]),
            "all_covered_by_city": bool(row[4]),
            "sibling_positive_overlap_m2": max(0.0, float(row[5])),
            "union_equals_city": bool(row[6]),
            "union_area_m2": float(row[7]),
            "city_area_m2": float(row[8]),
            "symmetric_difference_m2": max(0.0, float(row[9])),
        }
        evidence["fabric_status"] = (
            "COMPLETE"
            if evidence["observed_count"] == 8
            and evidence["all_valid"]
            and evidence["all_non_empty"]
            and evidence["all_polygonal"]
            and evidence["all_covered_by_city"]
            and evidence["sibling_positive_overlap_m2"] == 0.0
            and evidence["union_equals_city"]
            else "PARTIAL"
        )
        return evidence

    def preview_city(self, city_id: str) -> IncrementalCityDistrictPlan:
        city = self.engine.load_city(str(city_id).strip())
        sources = sources_for_city_source_record(self.source_path, city.source_record_id)
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
                if identity.parent_source_record_id != city.source_record_id:
                    raise RuntimeError("PARENT_CITY_BINDING_MISMATCH")
                item = self._realize(source, city)
                item["identityParentageMatch"] = True
                item["sourceContractMatch"] = True
                realized.append(item)
            except Exception as exc:
                rejected.append(
                    {
                        "districtId": source.administrative_area_id,
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
            overlap = overlaps.get(str(item["districtId"]), 0.0)
            item = dict(item)
            item["siblingPositiveOverlapM2"] = overlap
            if overlap == 0.0:
                item["qualificationStatus"] = "QUALIFIED"
                item["rejectionCode"] = None
            else:
                item["qualificationStatus"] = "REJECTED"
                item["rejectionCode"] = "SIBLING_POSITIVE_AREA_CONFLICT"
            feature_fingerprint = _canonical(
                {
                    "planId": PLAN_ID,
                    "districtId": item["districtId"],
                    "parentCityId": city.city_id,
                    "parentCityGeometryId": city.city_geometry_id,
                    "parentCityGeometrySha256": city.geometry_sha256,
                    "sourceGeometrySha256": item["sourceGeometrySha256"],
                    "geometrySha256": item["geometrySha256"],
                    "siblingPositiveOverlapM2": overlap,
                    "qualificationStatus": item["qualificationStatus"],
                }
            )
            item["featureFingerprint"] = feature_fingerprint
            candidates.append(item)

        for item in rejected:
            item["featureFingerprint"] = _canonical(
                {
                    "planId": PLAN_ID,
                    "districtId": item["districtId"],
                    "parentCityId": city.city_id,
                    "parentCityGeometryId": city.city_geometry_id,
                    "parentCityGeometrySha256": city.geometry_sha256,
                    "sourceGeometrySha256": item["sourceGeometrySha256"],
                    "qualificationStatus": "REJECTED",
                    "rejectionCode": item["rejectionCode"],
                }
            )
            candidates.append(item)

        candidates.sort(key=lambda item: str(item["districtId"]))
        fabric = self._fabric(city, realized)
        member_set = tuple(
            sorted(
                (
                    {
                        "districtId": str(item["districtId"]),
                        "geometryId": str(item["geometryId"]),
                        "geometrySha256": str(item["geometrySha256"]),
                    }
                    for item in realized
                ),
                key=lambda row: row["districtId"],
            )
        )
        member_sha = _canonical(member_set)
        body = {
            "databaseName": self.database_name,
            "environmentName": self.environment_name,
            "repositoryRevision": self.repository_revision,
            "effectiveDate": self.effective_date,
            "parentCityId": city.city_id,
            "parentCityName": city.canonical_name,
            "regionCode": city.region_code,
            "parentCitySourceRecordId": city.source_record_id,
            "parentCityGeometryId": city.city_geometry_id,
            "parentCityGeometrySha256": city.geometry_sha256,
            "partitionQualificationId": partition_qualification_id(city.city_id),
            "districtGeometrySetSha256": member_sha,
            "districtMemberSet": member_set,
            "districts": tuple(candidates),
            "fabric": fabric,
        }
        body["fingerprint"] = _canonical({"planId": PLAN_ID, "planVersion": PLAN_VERSION, **body})
        return IncrementalCityDistrictPlan(body)

    def _receipt_exists(self, fingerprint: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM geography.nngla_execution_receipt
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
                FROM geography.nngla_city_district_feature_publication
                WHERE administrative_area_id=%s
                  AND publication_id=%s
                  AND publication_status='PUBLISHED'
                """,
                (item["districtId"], item["publicationId"]),
            )
            return cursor.fetchone() is not None

    def _write_receipt(
        self,
        item: dict[str, object],
        *,
        submitter: str,
        approver: str,
        status: str,
        inserted: int,
        reused: int,
        failed: int,
        publication_ready: bool,
        detail: dict[str, object],
    ) -> None:
        now = datetime.now(timezone.utc)
        fingerprint = str(item["featureFingerprint"])
        execution_id = _execution_id(fingerprint)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_receipt(
                  execution_id,plan_id,plan_version,fingerprint_sha256,
                  database_name,environment_name,runtime_mode,repository_revision,
                  source_sha256,submitter_actor_id,approver_actor_id,
                  selected_count,inserted_count,reused_count,quarantined_count,
                  failed_count,status,started_at,completed_at
                ) VALUES (
                  %s,%s,%s,%s,current_database(),%s,'production',%s,%s,%s,%s,
                  1,%s,%s,0,%s,%s,%s,%s
                )
                """,
                (
                    execution_id, PLAN_ID, PLAN_VERSION, fingerprint,
                    self.environment_name, self.repository_revision,
                    str(item["sourceDatasetSha256"]), submitter, approver,
                    inserted, reused, failed, status, now, now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_item(
                  execution_id,source_record_id,canonical_id,outcome,
                  publication_ready,detail
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    execution_id,
                    str(item["sourceRecordId"]),
                    str(item["districtId"]),
                    status,
                    publication_ready,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )

    def _persist_qualified(self, plan: IncrementalCityDistrictPlan, item: dict[str, object], submitter: str, approver: str) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            if not self._feature_public_exists(item):
                raise RuntimeError("CITY_DISTRICT execution receipt exists but public feature is absent")
            return "REUSED"
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT district_geometry_id,geometry_sha256
                FROM geography.nngla_city_district_geometry_record
                WHERE administrative_area_id=%s
                  AND effective_to IS NULL
                  AND qualification_status='QUALIFIED'
                """,
                (item["districtId"],),
            )
            current = cursor.fetchone()
            geometry_inserted = False
            if current is None:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_city_district_geometry_record(
                      district_geometry_id,administrative_area_id,parent_city_id,parent_city_geometry_id,
                      parent_city_geometry_sha256,canonical_name,source_record_id,parent_source_record_id,
                      source_dataset_id,source_dataset_version,source_path_reference,source_dataset_sha256,
                      source_geometry_sha256,realization_method,realization_version,geometry_type_code,crs_code,
                      geometry,area_m2,area_km2,perimeter_m,perimeter_km,label_point,geometry_sha256,
                      qualification_status,effective_from
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,'NG-CRS-EPSG4326',
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,%s,%s,%s,
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,'QUALIFIED',%s
                    )
                    """,
                    (
                        item["geometryId"], item["districtId"], plan.payload["parentCityId"],
                        plan.payload["parentCityGeometryId"], plan.payload["parentCityGeometrySha256"],
                        item["canonicalName"], item["sourceRecordId"], item["parentSourceRecordId"],
                        item["sourceDatasetId"], item["sourceDatasetVersion"], item["sourcePathReference"],
                        item["sourceDatasetSha256"], item["sourceGeometrySha256"], item["realizationMethod"],
                        item["geometryTypeCode"], json.dumps(item["geometry"], separators=(",", ":"), ensure_ascii=False),
                        item["areaM2"], item["areaKm2"], item["perimeterM"], item["perimeterKm"],
                        json.dumps(item["labelPoint"], separators=(",", ":"), ensure_ascii=False),
                        item["geometrySha256"], self.effective_date,
                    ),
                )
                geometry_inserted = True
            elif (str(current[0]), str(current[1])) != (str(item["geometryId"]), str(item["geometrySha256"])):
                raise RuntimeError("current CITY_DISTRICT geometry differs from approved feature plan")

            cursor.execute(
                """
                INSERT INTO geography.nngla_city_district_feature_qualification(
                  feature_qualification_id,administrative_area_id,district_geometry_id,geometry_sha256,
                  source_geometry_sha256,parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256,
                  identity_parentage_match,source_contract_match,is_valid,is_non_empty,is_polygonal,
                  covered_by_parent_city,sibling_positive_overlap_m2,feature_fingerprint_sha256,
                  qualification_status,rejection_code,policy_version,qualified_at
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,true,true,true,true,true,true,%s,%s,
                  'QUALIFIED',NULL,2,%s
                ) ON CONFLICT (feature_qualification_id) DO NOTHING
                """,
                (
                    item["featureQualificationId"], item["districtId"], item["geometryId"],
                    item["geometrySha256"], item["sourceGeometrySha256"], plan.payload["parentCityId"],
                    plan.payload["parentCityGeometryId"], plan.payload["parentCityGeometrySha256"],
                    item["siblingPositiveOverlapM2"], item["featureFingerprint"], datetime.now(timezone.utc),
                ),
            )
            cursor.execute(
                """
                SELECT publication_id
                FROM geography.nngla_city_district_feature_publication
                WHERE administrative_area_id=%s AND publication_status='PUBLISHED'
                """,
                (item["districtId"],),
            )
            existing_pub = cursor.fetchone()
            publication_inserted = False
            if existing_pub is None:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_city_district_feature_publication(
                      publication_id,administrative_area_id,district_geometry_id,
                      feature_qualification_id,publication_status,published_at
                    ) VALUES (%s,%s,%s,%s,'PUBLISHED',%s)
                    """,
                    (
                        item["publicationId"], item["districtId"], item["geometryId"],
                        item["featureQualificationId"], datetime.now(timezone.utc),
                    ),
                )
                publication_inserted = True
            elif str(existing_pub[0]) != str(item["publicationId"]):
                raise RuntimeError("current CITY_DISTRICT feature publication differs from approved plan")

        applied = geometry_inserted or publication_inserted
        self._write_receipt(
            item,
            submitter=submitter,
            approver=approver,
            status="APPLIED" if applied else "REUSED",
            inserted=1 if applied else 0,
            reused=0 if applied else 1,
            failed=0,
            publication_ready=True,
            detail={
                "parent_city_id": plan.payload["parentCityId"],
                "district_id": item["districtId"],
                "district_geometry_id": item["geometryId"],
                "feature_qualification_id": item["featureQualificationId"],
                "publication_id": item["publicationId"],
                "geometry_sha256": item["geometrySha256"],
                "fabric_status": plan.payload["fabric"]["fabric_status"],
            },
        )
        return "APPLIED" if applied else "REUSED"

    def _persist_rejected(self, plan: IncrementalCityDistrictPlan, item: dict[str, object], submitter: str, approver: str) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            return "REUSED"
        self._write_receipt(
            item,
            submitter=submitter,
            approver=approver,
            status="FAILED",
            inserted=0,
            reused=0,
            failed=1,
            publication_ready=False,
            detail={
                "parent_city_id": plan.payload["parentCityId"],
                "district_id": item["districtId"],
                "rejection_code": item.get("rejectionCode"),
                "source_geometry_sha256": item["sourceGeometrySha256"],
                "fabric_status": plan.payload["fabric"]["fabric_status"],
            },
        )
        return "FAILED"

    def _persist_fabric(self, plan: IncrementalCityDistrictPlan) -> None:
        fabric = dict(plan.payload["fabric"])
        partition_status = "COMPLETE" if fabric["fabric_status"] == "COMPLETE" else "INCOMPLETE"
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_city_district_partition_qualification(
                  partition_qualification_id,parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256,
                  expected_district_count,observed_district_count,district_geometry_set_sha256,district_member_set,
                  all_valid,all_non_empty,all_polygonal,all_covered_by_city,sibling_positive_overlap_m2,
                  union_equals_city,union_area_m2,city_area_m2,symmetric_difference_m2,partition_status,
                  qualification_policy_version,effective_from
                ) VALUES (
                  %s,%s,%s,%s,8,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s
                )
                ON CONFLICT (partition_qualification_id) DO UPDATE SET
                  observed_district_count=EXCLUDED.observed_district_count,
                  district_geometry_set_sha256=EXCLUDED.district_geometry_set_sha256,
                  district_member_set=EXCLUDED.district_member_set,
                  all_valid=EXCLUDED.all_valid,
                  all_non_empty=EXCLUDED.all_non_empty,
                  all_polygonal=EXCLUDED.all_polygonal,
                  all_covered_by_city=EXCLUDED.all_covered_by_city,
                  sibling_positive_overlap_m2=EXCLUDED.sibling_positive_overlap_m2,
                  union_equals_city=EXCLUDED.union_equals_city,
                  union_area_m2=EXCLUDED.union_area_m2,
                  city_area_m2=EXCLUDED.city_area_m2,
                  symmetric_difference_m2=EXCLUDED.symmetric_difference_m2,
                  partition_status=EXCLUDED.partition_status,
                  effective_from=EXCLUDED.effective_from,
                  effective_to=NULL
                """,
                (
                    plan.payload["partitionQualificationId"], plan.payload["parentCityId"],
                    plan.payload["parentCityGeometryId"], plan.payload["parentCityGeometrySha256"],
                    fabric["observed_count"], plan.payload["districtGeometrySetSha256"],
                    json.dumps(plan.payload["districtMemberSet"], sort_keys=True, separators=(",", ":")),
                    fabric["all_valid"], fabric["all_non_empty"], fabric["all_polygonal"],
                    fabric["all_covered_by_city"], fabric["sibling_positive_overlap_m2"],
                    fabric["union_equals_city"], fabric["union_area_m2"], fabric["city_area_m2"],
                    fabric["symmetric_difference_m2"], partition_status, self.effective_date,
                ),
            )

    def execute_city(
        self,
        city_id: str,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ) -> IncrementalCityDistrictExecutionResult:
        submitter = str(submitter_actor_id).strip()
        approver = str(approver_actor_id).strip()
        if not submitter or not approver:
            raise ValueError("submitter and approver actor IDs are required")
        if submitter == approver:
            raise ValueError("submitter and approver must be different actors")

        plan = self.preview_city(city_id)
        if plan.fingerprint != str(approved_fingerprint).strip():
            raise RuntimeError("approved fingerprint does not match fresh CITY_DISTRICT incremental plan")
        if plan.confirmation_token != str(confirmation).strip():
            raise RuntimeError("confirmation token does not match fresh CITY_DISTRICT incremental plan")

        # Preview SELECTs open an implicit transaction in psycopg. Close it before
        # starting per-feature transactions so one failed child cannot poison the
        # other seven children.
        self.connection.commit()

        inserted = reused = failed = 0
        outcomes: list[dict[str, object]] = []
        for item in plan.payload["districts"]:
            try:
                with self.connection.transaction():
                    if item["qualificationStatus"] == "QUALIFIED":
                        outcome = self._persist_qualified(plan, item, submitter, approver)
                        if outcome == "APPLIED":
                            inserted += 1
                        else:
                            reused += 1
                    else:
                        outcome = self._persist_rejected(plan, item, submitter, approver)
                        if outcome == "FAILED":
                            failed += 1
                        else:
                            reused += 1
                outcomes.append({"districtId": item["districtId"], "outcome": outcome})
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
                                "parent_city_id": plan.payload["parentCityId"],
                                "district_id": item["districtId"],
                                "rejection_code": "PERSISTENCE_ERROR",
                                "error": str(exc),
                                "approved_feature_fingerprint": item["featureFingerprint"],
                            },
                        )
                except Exception as receipt_exc:
                    receipt_error = str(receipt_exc)
                outcome = {"districtId": item["districtId"], "outcome": "FAILED", "error": str(exc)}
                if receipt_error:
                    outcome["receiptError"] = receipt_error
                outcomes.append(outcome)

        with self.connection.transaction():
            self._persist_fabric(plan)

        return IncrementalCityDistrictExecutionResult(
            {
                "planId": PLAN_ID,
                "planVersion": PLAN_VERSION,
                "fingerprint": plan.fingerprint,
                "parentCityId": plan.payload["parentCityId"],
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
