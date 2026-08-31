"""Atomic national PostgreSQL persistence for governed TOWN settlement footprints."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from typing import Any

from .contracts import PLAN_ID, PLAN_VERSION, TownExecutionResult, TownNationalPlan
from .planning import execution_id


class PostgreSQLTownFootprintRealizationRepository:
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

    def current_publication_count(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM geography.nngla_town_public_read_v1")
            row = cursor.fetchone()
        return 0 if row is None else int(row[0])

    def replay(self, fingerprint: str) -> TownExecutionResult | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT r.execution_id,r.database_name,r.environment_name,
                       r.repository_revision,r.status,r.inserted_count,r.reused_count
                FROM geography.nngla_execution_receipt r
                JOIN geography.nngla_execution_item i USING (execution_id)
                WHERE r.fingerprint_sha256=%s
                  AND r.database_name=current_database()
                  AND r.environment_name=%s
                  AND r.plan_id=%s AND r.plan_version=%s
                """,
                (fingerprint, self.environment_name, PLAN_ID, PLAN_VERSION),
            )
            rows = list(cursor.fetchall())
        if not rows:
            return None
        if len(rows) != 1:
            raise RuntimeError("TOWN realization replay receipt is ambiguous")
        row = rows[0]
        return TownExecutionResult(
            execution_id=str(row[0]),
            fingerprint=fingerprint,
            database_name=str(row[1]),
            environment_name=str(row[2]),
            repository_revision=str(row[3]),
            status=str(row[4]),
            replayed=True,
            inserted_count=int(row[5]),
            reused_count=int(row[6]),
        )

    def insert_national_set(self, plan: TownNationalPlan) -> None:
        now = datetime.now(timezone.utc)
        with self.connection.cursor() as cursor:
            for item in plan.towns:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_town_settlement_footprint_record(
                      town_footprint_id,place_id,parent_place_id,canonical_name,source_place_code,
                      parent_source_place_code,geometry_role_code,legal_boundary_status,source_qualification_status,
                      source_dataset_id,source_dataset_version,source_generation_method,source_runtime_effect_scope,
                      source_path_reference,source_dataset_sha256,source_geometry_sha256,realization_version,
                      geometry_type_code,crs_code,geometry,area_m2,area_km2,perimeter_m,perimeter_km,label_point,
                      geometry_sha256,qualification_status,effective_from
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,'NG-CRS-EPSG4326',
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,%s,%s,%s,
                      ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,'QUALIFIED',%s
                    )
                    """,
                    (
                        item["footprintId"], item["placeId"], item["parentPlaceId"], item["canonicalName"],
                        item["sourcePlaceCode"], item["parentSourcePlaceCode"], item["geometryRoleCode"],
                        item["legalBoundaryStatus"], item["sourceQualificationStatus"], item["sourceDatasetId"],
                        item["sourceDatasetVersion"], item["sourceGenerationMethod"], item["sourceRuntimeEffectScope"],
                        item["sourcePathReference"], item["sourceDatasetSha256"], item["sourceGeometrySha256"],
                        item["geometryTypeCode"], json.dumps(item["geometry"], separators=(",", ":"), ensure_ascii=False),
                        item["areaM2"], item["areaKm2"], item["perimeterM"], item["perimeterKm"],
                        json.dumps(item["labelPoint"], separators=(",", ":"), ensure_ascii=False),
                        item["geometrySha256"], plan.effective_date,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_town_footprint_qualification(
                      qualification_id,place_id,town_footprint_id,geometry_sha256,is_valid,is_non_empty,
                      is_polygonal,identity_parentage_match,source_contract_match,qualification_status,
                      policy_version,qualified_at
                    ) VALUES (%s,%s,%s,%s,true,true,true,true,true,'QUALIFIED',1,%s)
                    """,
                    (
                        item["qualificationId"], item["placeId"], item["footprintId"],
                        item["geometrySha256"], now,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_town_publication(
                      publication_id,place_id,town_footprint_id,qualification_id,publication_status,published_at
                    ) VALUES (%s,%s,%s,%s,'PUBLISHED',%s)
                    """,
                    (
                        item["publicationId"], item["placeId"], item["footprintId"],
                        item["qualificationId"], now,
                    ),
                )

    def verify_public(self, plan: TownNationalPlan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT place_id,parent_place_id,town_footprint_id,geometry_sha256,
                       source_qualification_status,legal_boundary_status,qualification_status,publication_status
                FROM geography.nngla_town_public_read_v1 ORDER BY place_id
                """
            )
            rows = list(cursor.fetchall())
        if len(rows) != 120:
            raise RuntimeError("published TOWN set is not exactly 120")
        expected = {
            item["placeId"]: (
                item["parentPlaceId"], item["footprintId"], item["geometrySha256"],
                item["sourceQualificationStatus"], item["legalBoundaryStatus"],
            )
            for item in plan.towns
        }
        for row in rows:
            place_id = str(row[0])
            if place_id not in expected:
                raise RuntimeError("public view exposed unexpected TOWN identity")
            if tuple(str(value) for value in row[1:6]) != expected[place_id]:
                raise RuntimeError("public TOWN source/geometry does not match approved plan")
            if str(row[6]) != "QUALIFIED" or str(row[7]) != "PUBLISHED":
                raise RuntimeError("public TOWN qualification/publication status changed")

    def persist_execution(
        self,
        plan: TownNationalPlan,
        *,
        submitter_actor_id: str,
        approver_actor_id: str,
        status: str,
        inserted_count: int,
        reused_count: int,
    ) -> TownExecutionResult:
        eid = execution_id(plan.fingerprint)
        now = datetime.now(timezone.utc)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_receipt(
                  execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,
                  repository_revision,source_sha256,submitter_actor_id,approver_actor_id,selected_count,
                  inserted_count,reused_count,quarantined_count,failed_count,status,started_at,completed_at
                ) VALUES (%s,%s,%s,%s,current_database(),%s,'production',%s,%s,%s,%s,120,%s,%s,0,0,%s,%s,%s)
                """,
                (
                    eid, PLAN_ID, PLAN_VERSION, plan.fingerprint, self.environment_name,
                    plan.repository_revision, plan.source_dataset_sha256, submitter_actor_id,
                    approver_actor_id, inserted_count, reused_count, status, now, now,
                ),
            )
            for item in plan.towns:
                detail = {
                    "place_id": item["placeId"],
                    "parent_place_id": item["parentPlaceId"],
                    "parent_administrative_area_id": item["parentAdministrativeAreaId"],
                    "town_footprint_id": item["footprintId"],
                    "qualification_id": item["qualificationId"],
                    "publication_id": item["publicationId"],
                    "geometry_sha256": item["geometrySha256"],
                    "source_reference_sha256": plan.source_reference_sha256,
                    "source_footprint_sha256": plan.source_footprint_sha256,
                }
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_execution_item(
                      execution_id,source_record_id,canonical_id,outcome,publication_ready,detail
                    ) VALUES (%s,%s,%s,%s,true,%s::jsonb)
                    """,
                    (
                        eid, item["sourcePlaceCode"], item["placeId"], status,
                        json.dumps(detail, sort_keys=True, separators=(",", ":")),
                    ),
                )
        return TownExecutionResult(
            execution_id=eid,
            fingerprint=plan.fingerprint,
            database_name=plan.database_name,
            environment_name=plan.environment_name,
            repository_revision=plan.repository_revision,
            status=status,
            replayed=False,
            inserted_count=inserted_count,
            reused_count=reused_count,
        )


def require_identity_parentage(source, identity):
    """Compatibility helper retained for the initial focused tests."""
    if source.place_id != identity.place_id or source.parent_source_place_code != identity.parent_source_place_code:
        raise ValueError("refusing TOWN write: identity/parentage mismatch")
    return True
