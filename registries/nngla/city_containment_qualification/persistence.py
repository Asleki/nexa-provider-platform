"""Atomic PostgreSQL persistence for P006.7.11.15.8.1."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from typing import Any

from registries.nngla.city_realization.persistence import PostgreSQLCityRealizationRepository

from .contracts import (
    CONTAINMENT_PLAN_ID,
    CONTAINMENT_PLAN_VERSION,
    CityContainmentExecutionResult,
)
from .planning import execution_id


class PostgreSQLCityContainmentQualificationRepository:
    def __init__(self, connection: Any, *, environment_name: str) -> None:
        if connection is None:
            raise TypeError("connection is required")
        normalized = str(environment_name).strip()
        if not normalized:
            raise ValueError("environment_name is required")
        self.connection = connection
        self.environment_name = normalized
        self._city = PostgreSQLCityRealizationRepository(
            connection,
            environment_name=normalized,
        )

    @property
    def database_name(self) -> str:
        return self._city.database_name

    @contextmanager
    def transaction(self):
        with self._city.transaction():
            yield self

    def current_city_authority(self, city_id: str):
        return self._city.current_city_authority(city_id)

    def current_qualification(self, city_id: str):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT qualification_id,city_geometry_id,realized_geometry_sha256,
                       parent_region_id,parent_region_geometry_id,
                       parent_region_geometry_sha256,realization_method,
                       realization_version,qualification_status,
                       qualification_basis_code,qualification_policy_version,
                       absolute_residue_max_m2,ratio_residue_max,effective_from
                FROM geography.nngla_city_parent_containment_qualification
                WHERE administrative_area_id=%s
                  AND effective_to IS NULL
                """,
                (city_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) > 1:
            raise RuntimeError(f"multiple current CITY containment qualifications found: {city_id}")
        return None if not rows else tuple(rows[0])

    def replay(self, fingerprint: str) -> CityContainmentExecutionResult | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.execution_id,r.database_name,r.environment_name,
                       r.repository_revision,r.status,r.inserted_count,r.reused_count,
                       i.detail
                FROM geography.nngla_execution_receipt AS r
                JOIN geography.nngla_execution_item AS i USING (execution_id)
                WHERE r.fingerprint_sha256=%s
                  AND r.database_name=current_database()
                  AND r.environment_name=%s
                  AND r.plan_id=%s
                  AND r.plan_version=%s
                """,
                (
                    fingerprint,
                    self.environment_name,
                    CONTAINMENT_PLAN_ID,
                    CONTAINMENT_PLAN_VERSION,
                ),
            )
            rows = list(cursor.fetchall())
        if not rows:
            return None
        if len(rows) != 1:
            raise RuntimeError("CITY containment qualification replay receipt is ambiguous")
        row = rows[0]
        detail = row[7] if isinstance(row[7], dict) else json.loads(str(row[7]))
        return CityContainmentExecutionResult(
            execution_id=str(row[0]),
            fingerprint=fingerprint,
            city_id=str(detail["city_id"]),
            qualification_id=str(detail["qualification_id"]),
            qualification_status=str(detail["qualification_status"]),
            qualification_basis_code=str(detail["qualification_basis_code"]),
            city_geometry_id=str(detail["city_geometry_id"]),
            publication_id=str(detail["publication_id"]),
            database_name=str(row[1]),
            environment_name=str(row[2]),
            repository_revision=str(row[3]),
            status=str(row[4]),
            replayed=True,
            inserted_geometry_count=int(detail.get("inserted_geometry_count", 0)),
            inserted_qualification_count=int(detail.get("inserted_qualification_count", 0)),
            inserted_publication_count=int(detail.get("inserted_publication_count", 0)),
            reused_geometry_count=int(row[6]),
        )

    def insert_qualification(self, plan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO geography.nngla_city_parent_containment_qualification(
                    qualification_id,administrative_area_id,parent_region_id,
                    parent_region_geometry_id,parent_region_geometry_sha256,
                    source_record_id,source_dataset_id,source_dataset_version,
                    source_dataset_sha256,source_geometry_sha256,
                    realization_method,realization_version,city_geometry_id,
                    realized_geometry_sha256,
                    source_valid,source_non_empty,source_geometry_type,
                    source_strict_covered,source_area_m2,source_outside_parent_m2,
                    source_outside_parent_ratio,normalized_valid,
                    normalized_non_empty,normalized_geometry_type,
                    normalized_strict_covered,normalized_area_m2,
                    normalized_outside_parent_m2,normalized_outside_parent_ratio,
                    area_removed_m2,area_removed_ratio,label_point_covered,
                    qualification_basis_code,qualification_status,
                    qualification_policy_version,absolute_residue_max_m2,
                    ratio_residue_max,effective_from
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    plan.qualification_id,
                    plan.city_id,
                    plan.parent_region_id,
                    plan.parent_region_geometry_id,
                    plan.parent_region_geometry_sha256,
                    plan.source_record_id,
                    plan.source_dataset_id,
                    plan.source_dataset_version,
                    plan.source_dataset_sha256,
                    plan.source_geometry_sha256,
                    plan.realization_method,
                    plan.realization_version,
                    plan.city_geometry_id,
                    plan.geometry_sha256,
                    plan.source_valid,
                    plan.source_non_empty,
                    plan.source_geometry_type,
                    plan.source_strict_covered,
                    plan.source_area_m2,
                    plan.source_outside_parent_m2,
                    plan.source_outside_parent_ratio,
                    plan.normalized_valid,
                    plan.normalized_non_empty,
                    plan.normalized_geometry_type,
                    plan.normalized_strict_covered,
                    plan.area_m2,
                    plan.normalized_outside_parent_m2,
                    plan.normalized_outside_parent_ratio,
                    plan.area_removed_m2,
                    plan.area_removed_ratio,
                    plan.label_point_covered,
                    plan.qualification_basis_code,
                    plan.qualification_status,
                    plan.qualification_policy_version,
                    plan.absolute_residue_max_m2,
                    plan.ratio_residue_max,
                    plan.effective_date,
                ),
            )

    def insert_geometry(self, plan) -> None:
        self._city.insert_geometry(plan)

    def insert_publication(self, plan) -> None:
        self._city.insert_publication(plan)

    def verify_public(self, plan) -> None:
        self._city.verify_public(plan)

    def verify_qualification(self, plan) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT qualification_id,administrative_area_id,city_geometry_id,
                       realized_geometry_sha256,parent_region_id,
                       parent_region_geometry_id,parent_region_geometry_sha256,
                       qualification_status,qualification_basis_code,
                       qualification_policy_version,normalized_outside_parent_m2,
                       normalized_outside_parent_ratio,absolute_residue_max_m2,
                       ratio_residue_max
                FROM geography.nngla_city_parent_containment_read_v1
                WHERE qualification_id=%s
                """,
                (plan.qualification_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise RuntimeError("CITY containment qualification is not uniquely visible")
        row = rows[0]
        actual = (
            str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]),
            str(row[5]), str(row[6]), str(row[7]), str(row[8]), int(row[9]),
        )
        expected = (
            plan.qualification_id, plan.city_id, plan.city_geometry_id,
            plan.geometry_sha256, plan.parent_region_id,
            plan.parent_region_geometry_id, plan.parent_region_geometry_sha256,
            plan.qualification_status, plan.qualification_basis_code,
            plan.qualification_policy_version,
        )
        if actual != expected:
            raise RuntimeError("stored CITY containment qualification differs from approved plan")
        numeric = (
            float(row[10]), float(row[11]), float(row[12]), float(row[13])
        )
        expected_numeric = (
            plan.normalized_outside_parent_m2,
            plan.normalized_outside_parent_ratio,
            plan.absolute_residue_max_m2,
            plan.ratio_residue_max,
        )
        if numeric != expected_numeric:
            raise RuntimeError("stored CITY containment measurements differ from approved plan")

    def persist_execution(
        self,
        plan,
        *,
        submitter_actor_id: str,
        approver_actor_id: str,
        status: str,
        inserted_geometry_count: int,
        inserted_qualification_count: int,
        inserted_publication_count: int,
        reused_geometry_count: int,
    ) -> CityContainmentExecutionResult:
        eid = execution_id(plan.fingerprint)
        now = datetime.now(timezone.utc)
        publication_ready = plan.qualification_status == "QUALIFIED"
        detail = {
            "city_id": plan.city_id,
            "qualification_id": plan.qualification_id,
            "qualification_status": plan.qualification_status,
            "qualification_basis_code": plan.qualification_basis_code,
            "qualification_policy_version": plan.qualification_policy_version,
            "city_geometry_id": plan.city_geometry_id,
            "publication_id": plan.publication_id,
            "parent_region_id": plan.parent_region_id,
            "parent_region_geometry_id": plan.parent_region_geometry_id,
            "parent_region_geometry_sha256": plan.parent_region_geometry_sha256,
            "source_geometry_sha256": plan.source_geometry_sha256,
            "geometry_sha256": plan.geometry_sha256,
            "source_outside_parent_m2": plan.source_outside_parent_m2,
            "source_outside_parent_ratio": plan.source_outside_parent_ratio,
            "normalized_outside_parent_m2": plan.normalized_outside_parent_m2,
            "normalized_outside_parent_ratio": plan.normalized_outside_parent_ratio,
            "absolute_residue_max_m2": plan.absolute_residue_max_m2,
            "ratio_residue_max": plan.ratio_residue_max,
            "inserted_geometry_count": inserted_geometry_count,
            "inserted_qualification_count": inserted_qualification_count,
            "inserted_publication_count": inserted_publication_count,
            "reused_geometry_count": reused_geometry_count,
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
                    CONTAINMENT_PLAN_ID,
                    CONTAINMENT_PLAN_VERSION,
                    plan.fingerprint,
                    self.environment_name,
                    plan.repository_revision,
                    plan.source_dataset_sha256,
                    submitter_actor_id,
                    approver_actor_id,
                    0 if status == "REUSED" else 1,
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
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    eid,
                    plan.source_record_id,
                    plan.city_id,
                    plan.qualification_status,
                    publication_ready,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )
        return CityContainmentExecutionResult(
            execution_id=eid,
            fingerprint=plan.fingerprint,
            city_id=plan.city_id,
            qualification_id=plan.qualification_id,
            qualification_status=plan.qualification_status,
            qualification_basis_code=plan.qualification_basis_code,
            city_geometry_id=plan.city_geometry_id,
            publication_id=plan.publication_id,
            database_name=plan.database_name,
            environment_name=plan.environment_name,
            repository_revision=plan.repository_revision,
            status=status,
            replayed=False,
            inserted_geometry_count=inserted_geometry_count,
            inserted_qualification_count=inserted_qualification_count,
            inserted_publication_count=inserted_publication_count,
            reused_geometry_count=reused_geometry_count,
        )
