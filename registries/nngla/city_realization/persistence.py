"""Atomic PostgreSQL persistence for governed CITY realization/publication."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from typing import Any

from .contracts import (
    CityExecutionResult,
    CityRealizationPlan,
    CurrentCityAuthority,
    PLAN_ID,
    PLAN_VERSION,
)
from .planning import execution_id
from .source import canonical_json_sha256


class PostgreSQLCityRealizationRepository:
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
        # Close any earlier implicit read transaction before the explicit writer.
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

    def current_city_authority(self, city_id: str) -> CurrentCityAuthority | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT city_geometry_id,geometry_sha256,parent_region_id,
                       parent_region_geometry_id,parent_region_geometry_sha256,
                       realization_method,realization_version,effective_from
                FROM geography.nngla_city_geometry_record
                WHERE administrative_area_id=%s
                  AND effective_to IS NULL
                  AND qualification_status='QUALIFIED'
                """,
                (city_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) > 1:
            raise RuntimeError(f"multiple current qualified CITY geometries found: {city_id}")
        if not rows:
            return None
        row = rows[0]
        city_geometry_id = str(row[0])
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT publication_id,publication_status
                FROM geography.nngla_city_publication
                WHERE administrative_area_id=%s
                  AND city_geometry_id=%s
                ORDER BY created_at,publication_id
                """,
                (city_id, city_geometry_id),
            )
            publication_rows = list(cursor.fetchall())
        if len(publication_rows) > 1:
            raise RuntimeError(
                f"multiple publication records exist for current initial CITY geometry: {city_id}"
            )
        publication_id = None if not publication_rows else str(publication_rows[0][0])
        publication_status = None if not publication_rows else str(publication_rows[0][1])
        return CurrentCityAuthority(
            city_geometry_id=city_geometry_id,
            geometry_sha256=str(row[1]),
            parent_region_id=str(row[2]),
            parent_region_geometry_id=str(row[3]),
            parent_region_geometry_sha256=str(row[4]),
            realization_method=str(row[5]),
            realization_version=int(row[6]),
            effective_from=str(row[7]),
            publication_id=publication_id,
            publication_status=publication_status,
        )

    def replay(self, fingerprint: str) -> CityExecutionResult | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT execution_id,database_name,environment_name,repository_revision,
                       status,inserted_count,reused_count,
                       detail->>'city_id',detail->>'city_geometry_id',detail->>'publication_id'
                FROM geography.nngla_execution_receipt AS r
                JOIN geography.nngla_execution_item AS i USING (execution_id)
                WHERE r.fingerprint_sha256=%s
                  AND r.database_name=current_database()
                  AND r.environment_name=%s
                  AND r.plan_id=%s
                  AND r.plan_version=%s
                """,
                (fingerprint, self.environment_name, PLAN_ID, PLAN_VERSION),
            )
            rows = list(cursor.fetchall())
        if not rows:
            return None
        if len(rows) != 1:
            raise RuntimeError("CITY realization replay receipt is ambiguous")
        row = rows[0]
        return CityExecutionResult(
            execution_id=str(row[0]),
            fingerprint=fingerprint,
            city_id=str(row[7]),
            city_geometry_id=str(row[8]),
            publication_id=str(row[9]),
            database_name=str(row[1]),
            environment_name=str(row[2]),
            repository_revision=str(row[3]),
            status=str(row[4]),
            replayed=True,
            inserted_geometry_count=int(row[5]),
            reused_geometry_count=int(row[6]),
        )

    def insert_geometry(self, plan: CityRealizationPlan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_city_geometry_record(
                    city_geometry_id,administrative_area_id,parent_region_id,
                    parent_region_geometry_id,parent_region_geometry_sha256,
                    canonical_name,source_record_id,source_dataset_id,
                    source_dataset_version,source_path_reference,
                    source_dataset_sha256,source_geometry_sha256,
                    realization_method,realization_version,geometry_type_code,
                    crs_code,geometry,area_m2,area_km2,perimeter_m,perimeter_km,
                    label_point,geometry_sha256,qualification_status,effective_from
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,%s,%s,%s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,'QUALIFIED',%s
                )
                """,
                (
                    plan.city_geometry_id,
                    plan.city_id,
                    plan.parent_region_id,
                    plan.parent_region_geometry_id,
                    plan.parent_region_geometry_sha256,
                    plan.canonical_name,
                    plan.source_record_id,
                    plan.source_dataset_id,
                    plan.source_dataset_version,
                    plan.source_path_reference,
                    plan.source_dataset_sha256,
                    plan.source_geometry_sha256,
                    plan.realization_method,
                    plan.realization_version,
                    plan.geometry_type_code,
                    plan.crs_code,
                    json.dumps(plan.geometry, separators=(",", ":"), ensure_ascii=False),
                    plan.area_m2,
                    plan.area_km2,
                    plan.perimeter_m,
                    plan.perimeter_km,
                    json.dumps(plan.label_point, separators=(",", ":"), ensure_ascii=False),
                    plan.geometry_sha256,
                    plan.effective_date,
                ),
            )

    def insert_publication(self, plan: CityRealizationPlan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_city_publication(
                    publication_id,administrative_area_id,city_geometry_id,
                    publication_status,published_at
                ) VALUES (%s,%s,%s,'PUBLISHED',%s)
                """,
                (
                    plan.publication_id,
                    plan.city_id,
                    plan.city_geometry_id,
                    datetime.now(timezone.utc),
                ),
            )

    def verify_public(self, plan: CityRealizationPlan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT city_id,city_geometry_id,parent_region_id,
                       parent_region_geometry_id,parent_region_geometry_sha256,
                       geometry_sha256,realization_method,realization_version,
                       publication_id,publication_status,
                       ST_AsGeoJSON(geometry,15)::jsonb,area_m2,perimeter_m,
                       label_longitude,label_latitude
                FROM geography.nngla_city_public_read_v1
                WHERE city_id=%s
                """,
                (plan.city_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise RuntimeError(f"published CITY is not uniquely visible in public view: {plan.city_id}")
        row = rows[0]
        actual = (
            str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]),
            str(row[5]), str(row[6]), int(row[7]), str(row[8]), str(row[9]),
        )
        expected = (
            plan.city_id, plan.city_geometry_id, plan.parent_region_id,
            plan.parent_region_geometry_id, plan.parent_region_geometry_sha256,
            plan.geometry_sha256, plan.realization_method, plan.realization_version,
            plan.publication_id, "PUBLISHED",
        )
        if actual != expected:
            raise RuntimeError("public CITY row does not match approved realization plan")
        geometry = row[10] if isinstance(row[10], dict) else json.loads(str(row[10]))
        if canonical_json_sha256(geometry) != plan.geometry_sha256:
            raise RuntimeError("stored public CITY geometry bytes do not match approved geometry hash")
        if float(row[11]) != plan.area_m2 or float(row[12]) != plan.perimeter_m:
            raise RuntimeError("stored public CITY measurements do not match approved plan")
        coordinates = plan.label_point.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise RuntimeError("approved CITY label point is malformed")
        if float(row[13]) != float(coordinates[0]) or float(row[14]) != float(coordinates[1]):
            raise RuntimeError("stored public CITY label point does not match approved plan")

    def persist_execution(
        self,
        plan: CityRealizationPlan,
        *,
        submitter_actor_id: str,
        approver_actor_id: str,
        status: str,
        inserted_geometry_count: int,
        reused_geometry_count: int,
    ) -> CityExecutionResult:
        eid = execution_id(plan.fingerprint)
        now = datetime.now(timezone.utc)
        detail = {
            "city_id": plan.city_id,
            "city_geometry_id": plan.city_geometry_id,
            "publication_id": plan.publication_id,
            "parent_region_id": plan.parent_region_id,
            "parent_region_geometry_id": plan.parent_region_geometry_id,
            "source_record_id": plan.source_record_id,
            "source_dataset_sha256": plan.source_dataset_sha256,
            "source_geometry_sha256": plan.source_geometry_sha256,
            "geometry_sha256": plan.geometry_sha256,
            "realization_method": plan.realization_method,
            "realization_version": plan.realization_version,
            "planned_action": plan.planned_action,
        }
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_receipt(
                    execution_id,plan_id,plan_version,fingerprint_sha256,
                    database_name,environment_name,runtime_mode,
                    repository_revision,source_sha256,
                    submitter_actor_id,approver_actor_id,
                    selected_count,inserted_count,reused_count,quarantined_count,
                    failed_count,status,started_at,completed_at
                ) VALUES (
                    %s,%s,%s,%s,current_database(),%s,'production',%s,%s,%s,%s,
                    1,%s,%s,0,0,%s,%s,%s
                )
                """,
                (
                    eid,
                    PLAN_ID,
                    PLAN_VERSION,
                    plan.fingerprint,
                    self.environment_name,
                    plan.repository_revision,
                    plan.source_dataset_sha256,
                    submitter_actor_id,
                    approver_actor_id,
                    inserted_geometry_count,
                    reused_geometry_count,
                    status,
                    now,
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_item(
                    execution_id,source_record_id,canonical_id,outcome,
                    publication_ready,detail
                ) VALUES (%s,%s,%s,%s,true,%s::jsonb)
                """,
                (
                    eid,
                    plan.source_record_id,
                    plan.city_id,
                    status,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )
        return CityExecutionResult(
            execution_id=eid,
            fingerprint=plan.fingerprint,
            city_id=plan.city_id,
            city_geometry_id=plan.city_geometry_id,
            publication_id=plan.publication_id,
            database_name=plan.database_name,
            environment_name=plan.environment_name,
            repository_revision=plan.repository_revision,
            status=status,
            replayed=False,
            inserted_geometry_count=inserted_geometry_count,
            reused_geometry_count=reused_geometry_count,
        )
