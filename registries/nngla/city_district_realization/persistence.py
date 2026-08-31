"""Atomic per-CITY PostgreSQL persistence for CITY_DISTRICT publication."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from typing import Any

from .contracts import CityDistrictExecutionResult, CityDistrictPlan, PLAN_ID, PLAN_VERSION
from .planning import execution_id


class PostgreSQLCityDistrictRealizationRepository:
    def __init__(self, connection: Any, *, environment_name: str) -> None:
        if connection is None:
            raise TypeError("connection is required")
        if not str(environment_name).strip():
            raise ValueError("environment_name is required")
        self.connection = connection
        self.environment_name = str(environment_name).strip()

    @property
    def database_name(self) -> str:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
        if row is None or not str(row[0]).strip():
            raise RuntimeError("current PostgreSQL database name is unavailable")
        return str(row[0])

    @contextmanager
    def transaction(self):
        self.connection.commit()
        transaction = getattr(self.connection, "transaction", None)
        if callable(transaction):
            with transaction():
                yield self
            return
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def current_publication_count(self, parent_city_id: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM geography.nngla_city_district_public_read_v1 WHERE parent_city_id=%s",
                (parent_city_id,),
            )
            row = cursor.fetchone()
        return 0 if row is None else int(row[0])

    def replay(self, fingerprint: str) -> CityDistrictExecutionResult | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.execution_id,r.database_name,r.environment_name,r.repository_revision,
                       r.status,r.inserted_count,r.reused_count,i.detail->>'parent_city_id'
                FROM geography.nngla_execution_receipt r
                JOIN geography.nngla_execution_item i USING (execution_id)
                WHERE r.fingerprint_sha256=%s
                  AND r.database_name=current_database()
                  AND r.environment_name=%s
                  AND r.plan_id=%s AND r.plan_version=%s
                ORDER BY i.canonical_id
                """,
                (fingerprint, self.environment_name, PLAN_ID, PLAN_VERSION),
            )
            rows = list(cursor.fetchall())
        if not rows:
            return None
        execution_ids = {str(row[0]) for row in rows}
        parent_ids = {str(row[7]) for row in rows}
        if len(execution_ids) != 1 or len(parent_ids) != 1:
            raise RuntimeError("CITY_DISTRICT replay receipt is ambiguous")
        first = rows[0]
        return CityDistrictExecutionResult(
            execution_id=str(first[0]),
            fingerprint=fingerprint,
            parent_city_id=next(iter(parent_ids)),
            database_name=str(first[1]),
            environment_name=str(first[2]),
            repository_revision=str(first[3]),
            status=str(first[4]),
            replayed=True,
            inserted_count=int(first[5]),
            reused_count=int(first[6]),
        )

    def insert_city_partition(self, plan: CityDistrictPlan) -> None:
        if plan.partition.get("partition_status") != "COMPLETE":
            raise RuntimeError("INCOMPLETE CITY_DISTRICT partition cannot be published")
        now = datetime.now(timezone.utc)
        with self.connection.cursor() as cursor:
            for item in plan.districts:
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
                        item["geometryId"], item["districtId"], plan.parent_city_id,
                        plan.parent_city_geometry_id, plan.parent_city_geometry_sha256,
                        item["canonicalName"], item["sourceRecordId"], item["parentSourceRecordId"],
                        item["sourceDatasetId"], item["sourceDatasetVersion"], item["sourcePathReference"],
                        item["sourceDatasetSha256"], item["sourceGeometrySha256"], item["realizationMethod"],
                        item["geometryTypeCode"], json.dumps(item["geometry"], separators=(",", ":"), ensure_ascii=False),
                        item["areaM2"], item["areaKm2"], item["perimeterM"], item["perimeterKm"],
                        json.dumps(item["labelPoint"], separators=(",", ":"), ensure_ascii=False),
                        item["geometrySha256"], plan.effective_date,
                    ),
                )

            part = plan.partition
            cursor.execute(
                """
                INSERT INTO geography.nngla_city_district_partition_qualification(
                  partition_qualification_id,parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256,
                  expected_district_count,observed_district_count,district_geometry_set_sha256,district_member_set,
                  all_valid,all_non_empty,all_polygonal,all_covered_by_city,sibling_positive_overlap_m2,
                  union_equals_city,union_area_m2,city_area_m2,symmetric_difference_m2,partition_status,
                  qualification_policy_version,effective_from
                ) VALUES (%s,%s,%s,%s,8,8,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,'COMPLETE',1,%s)
                """,
                (
                    plan.partition_qualification_id, plan.parent_city_id, plan.parent_city_geometry_id,
                    plan.parent_city_geometry_sha256, plan.district_geometry_set_sha256,
                    json.dumps(plan.district_member_set, sort_keys=True, separators=(",", ":")),
                    part["all_valid"], part["all_non_empty"], part["all_polygonal"], part["all_covered_by_city"],
                    part["sibling_positive_overlap_m2"], part["union_equals_city"], part["union_area_m2"],
                    part["city_area_m2"], part["symmetric_difference_m2"], plan.effective_date,
                ),
            )

            for item in plan.districts:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_city_district_publication(
                      publication_id,administrative_area_id,district_geometry_id,
                      partition_qualification_id,publication_status,published_at
                    ) VALUES (%s,%s,%s,%s,'PUBLISHED',%s)
                    """,
                    (
                        item["publicationId"], item["districtId"], item["geometryId"],
                        plan.partition_qualification_id, now,
                    ),
                )

    def verify_public(self, plan: CityDistrictPlan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT district_id,district_geometry_id,geometry_sha256,partition_status,
                       parent_city_geometry_id,parent_city_geometry_sha256,publication_status
                FROM geography.nngla_city_district_public_read_v1
                WHERE parent_city_id=%s ORDER BY district_id
                """,
                (plan.parent_city_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 8:
            raise RuntimeError("published CITY_DISTRICT set is not exactly eight")
        expected = {
            item["districtId"]: (item["geometryId"], item["geometrySha256"])
            for item in plan.districts
        }
        for row in rows:
            district_id = str(row[0])
            if district_id not in expected or (str(row[1]), str(row[2])) != expected[district_id]:
                raise RuntimeError("public CITY_DISTRICT geometry does not match approved plan")
            if str(row[3]) != "COMPLETE" or str(row[6]) != "PUBLISHED":
                raise RuntimeError("public CITY_DISTRICT partition/publication state changed")
            if (str(row[4]), str(row[5])) != (
                plan.parent_city_geometry_id,
                plan.parent_city_geometry_sha256,
            ):
                raise RuntimeError("public CITY_DISTRICT parent CITY version changed")

    def persist_execution(
        self,
        plan: CityDistrictPlan,
        *,
        submitter_actor_id: str,
        approver_actor_id: str,
        status: str,
        inserted_count: int,
        reused_count: int,
    ) -> CityDistrictExecutionResult:
        eid = execution_id(plan.fingerprint)
        now = datetime.now(timezone.utc)
        source_sha = str(plan.districts[0]["sourceDatasetSha256"])
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_receipt(
                  execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,
                  runtime_mode,repository_revision,source_sha256,submitter_actor_id,approver_actor_id,
                  selected_count,inserted_count,reused_count,quarantined_count,failed_count,status,
                  started_at,completed_at
                ) VALUES (%s,%s,%s,%s,current_database(),%s,'production',%s,%s,%s,%s,8,%s,%s,0,0,%s,%s,%s)
                """,
                (
                    eid, PLAN_ID, PLAN_VERSION, plan.fingerprint, self.environment_name,
                    plan.repository_revision, source_sha, submitter_actor_id, approver_actor_id,
                    inserted_count, reused_count, status, now, now,
                ),
            )
            for item in plan.districts:
                detail = {
                    "parent_city_id": plan.parent_city_id,
                    "partition_qualification_id": plan.partition_qualification_id,
                    "district_id": item["districtId"],
                    "district_geometry_id": item["geometryId"],
                    "publication_id": item["publicationId"],
                    "geometry_sha256": item["geometrySha256"],
                    "partition_status": plan.partition["partition_status"],
                }
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_execution_item(
                      execution_id,source_record_id,canonical_id,outcome,publication_ready,detail
                    ) VALUES (%s,%s,%s,%s,true,%s::jsonb)
                    """,
                    (
                        eid, item["sourceRecordId"], item["districtId"], status,
                        json.dumps(detail, sort_keys=True, separators=(",", ":")),
                    ),
                )
        return CityDistrictExecutionResult(
            execution_id=eid,
            fingerprint=plan.fingerprint,
            parent_city_id=plan.parent_city_id,
            database_name=plan.database_name,
            environment_name=plan.environment_name,
            repository_revision=plan.repository_revision,
            status=status,
            replayed=False,
            inserted_count=inserted_count,
            reused_count=reused_count,
        )
