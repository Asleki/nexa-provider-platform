"""Sequence-29 incremental TOWN settlement-footprint publication.

TOWN depends only on its published authoritative MUNICIPALITY. Each town is
qualified and published independently. Processing is grouped by municipality,
but a rejected town never blocks its siblings or any other municipality.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .contracts import TownIdentity
from .planning import canonical_sha256, publication_id, qualification_id, qualify_source, town_footprint_id
from .source import load_town_sources

PLAN_ID = "p006.7.11.15.9-seq29-town-feature-publication"
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
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _effective_date(value: str | None) -> str:
    return date.fromisoformat(str(value or date.today().isoformat())).isoformat()


def _execution_id(fingerprint: str) -> str:
    return f"nnglarun:seq29-town:{fingerprint}"


@dataclass(frozen=True, slots=True)
class IncrementalTownPlan:
    payload: dict[str, object]

    @property
    def fingerprint(self) -> str:
        return str(self.payload["fingerprint"])

    @property
    def database_name(self) -> str:
        return str(self.payload["databaseName"])

    @property
    def confirmation_token(self) -> str:
        return f"REALIZE-NNGLA-TOWN-INCREMENTAL::{self.database_name}::{self.fingerprint}"

    def as_dict(self) -> dict[str, object]:
        return {
            **self.payload,
            "planId": PLAN_ID,
            "planVersion": PLAN_VERSION,
            "confirmationToken": self.confirmation_token,
        }


@dataclass(frozen=True, slots=True)
class IncrementalTownExecutionResult:
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return dict(self.payload)


class IncrementalTownPublicationService:
    def __init__(
        self,
        connection: Any,
        *,
        footprint_path: Path,
        reference_path: Path,
        summary_path: Path,
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
        self.footprint_path = Path(footprint_path)
        self.reference_path = Path(reference_path)
        self.summary_path = Path(summary_path)
        self.environment_name = str(environment_name).strip()
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = _effective_date(effective_date)

    @property
    def database_name(self) -> str:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("current database is unavailable")
        return str(row[0])

    def _load_identity(self, place_id: str) -> TownIdentity:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.place_id,n.canonical_name,p.region_code,p.source_place_code,
                       p.parent_source_place_code,parent.place_id,parent.place_type_code,
                       admin.administrative_area_id,m.municipality_geometry_id,m.geometry_sha256
                FROM geography.nngla_place_reference AS p
                JOIN geography.nngla_geographic_name AS n
                  ON n.name_id=p.settlement_name_record_id
                JOIN geography.nngla_place_reference AS parent
                  ON parent.source_place_code=p.parent_source_place_code
                JOIN geography.nngla_administrative_area AS admin
                  ON admin.source_record_id=parent.source_place_code
                 AND admin.administrative_type_code='MUNICIPALITY'
                JOIN geography.nngla_municipality_public_read_v2 AS m
                  ON m.municipality_id=admin.administrative_area_id
                 AND m.publication_status='PUBLISHED'
                 AND m.qualification_status='QUALIFIED'
                WHERE p.place_id=%s
                  AND upper(p.place_type_code)='TOWN'
                  AND upper(parent.place_type_code)='MUNICIPALITY'
                """,
                (place_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise RuntimeError("PARENT_MUNICIPALITY_AUTHORITY_UNAVAILABLE")
        return TownIdentity(*(str(value) for value in rows[0]))

    def _realize(self, source, identity: TownIdentity) -> dict[str, object]:
        source_geojson = json.dumps(source.geometry, separators=(",", ":"), ensure_ascii=False)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH parent AS (
                  SELECT geometry
                  FROM geography.nngla_municipality_public_read_v2
                  WHERE municipality_id=%s
                    AND municipality_geometry_id=%s
                    AND geometry_sha256=%s
                    AND publication_status='PUBLISHED'
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                )
                SELECT
                  ST_IsValid(src.geometry),NOT ST_IsEmpty(src.geometry),ST_GeometryType(src.geometry),
                  ST_CoveredBy(src.geometry,parent.geometry),
                  ST_Area(src.geometry::geography),ST_Perimeter(src.geometry::geography),
                  ST_AsGeoJSON(src.geometry,15)::jsonb,
                  ST_AsGeoJSON(ST_PointOnSurface(src.geometry),15)::jsonb,
                  ST_CoveredBy(ST_PointOnSurface(src.geometry),src.geometry)
                FROM src CROSS JOIN parent
                """,
                (
                    identity.parent_administrative_area_id,
                    identity.parent_municipality_geometry_id,
                    identity.parent_municipality_geometry_sha256,
                    source_geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("PARENT_MUNICIPALITY_GEOMETRY_UNAVAILABLE")
        geometry_type = str(row[2]).removeprefix("ST_").upper()
        if not bool(row[0]) or not bool(row[1]) or geometry_type != "POLYGON":
            raise RuntimeError("TOWN_FOOTPRINT_INVALID_OR_NON_POLYGONAL")
        if not bool(row[3]):
            raise RuntimeError("PARENT_MUNICIPALITY_CONTAINMENT_FAILED")
        if not bool(row[8]):
            raise RuntimeError("LABEL_POINT_INVALID")
        area_m2 = float(row[4])
        perimeter_m = float(row[5])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise RuntimeError("NON_POSITIVE_MEASUREMENT")
        geometry = _json_object(row[6], "TOWN footprint")
        label_point = _json_object(row[7], "TOWN label point")
        return {
            "placeId": source.place_id,
            "canonicalName": source.canonical_name,
            "regionCode": source.region_code,
            "sourcePlaceCode": source.source_place_code,
            "parentSourcePlaceCode": source.parent_source_place_code,
            "parentPlaceId": identity.parent_place_id,
            "parentAdministrativeAreaId": identity.parent_administrative_area_id,
            "parentMunicipalityGeometryId": identity.parent_municipality_geometry_id,
            "parentMunicipalityGeometrySha256": identity.parent_municipality_geometry_sha256,
            "geometryRoleCode": source.geometry_role_code,
            "legalBoundaryStatus": source.legal_boundary_status,
            "sourceQualificationStatus": source.qualification_status,
            "sourceGenerationMethod": source.source_basis,
            "sourceRuntimeEffectScope": source.runtime_effect_scope,
            "sourceDatasetId": source.dataset_id,
            "sourceDatasetVersion": source.dataset_version,
            "sourcePathReference": source.source_path_reference,
            "sourceDatasetSha256": source.source_dataset_sha256,
            "sourceReferenceSha256": source.source_reference_sha256,
            "sourceFootprintSha256": source.source_footprint_sha256,
            "sourceGeometrySha256": source.source_geometry_sha256,
            "footprintId": town_footprint_id(source.place_id),
            "qualificationId": qualification_id(source.place_id),
            "publicationId": publication_id(source.place_id),
            "geometryTypeCode": geometry_type,
            "geometry": geometry,
            "geometrySha256": canonical_sha256(geometry),
            "labelPoint": label_point,
            "areaM2": area_m2,
            "areaKm2": area_m2 / 1_000_000.0,
            "perimeterM": perimeter_m,
            "perimeterKm": perimeter_m / 1000.0,
            "qualificationStatus": "QUALIFIED",
            "rejectionCode": None,
        }

    def _published_municipality(self, municipality_id: str) -> dict[str, str]:
        normalized = str(municipality_id).strip()
        if not normalized:
            raise ValueError("municipality_id is required")
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT municipality_id,source_record_id,municipality_geometry_id,
                       geometry_sha256,canonical_name,parent_region_id
                FROM geography.nngla_municipality_public_read_v2
                WHERE municipality_id=%s
                  AND qualification_status='QUALIFIED'
                  AND publication_status='PUBLISHED'
                """,
                (normalized,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise RuntimeError("PUBLISHED_PARENT_MUNICIPALITY_UNAVAILABLE")
        return {
            "municipalityId": str(rows[0][0]),
            "sourceRecordId": str(rows[0][1]),
            "geometryId": str(rows[0][2]),
            "geometrySha256": str(rows[0][3]),
            "canonicalName": str(rows[0][4]),
            "parentRegionId": str(rows[0][5]),
        }

    def _build_plan(
        self,
        sources,
        *,
        scope: dict[str, object],
    ) -> IncrementalTownPlan:
        candidates: list[dict[str, object]] = []
        for source in sources:
            try:
                identity = self._load_identity(source.place_id)
                qualify_source(source, identity)
                item = self._realize(source, identity)
            except Exception as exc:
                item = {
                    "placeId": source.place_id,
                    "canonicalName": source.canonical_name,
                    "sourcePlaceCode": source.source_place_code,
                    "parentSourcePlaceCode": source.parent_source_place_code,
                    "parentAdministrativeAreaId": scope.get("municipalityId"),
                    "sourceDatasetSha256": source.source_dataset_sha256,
                    "sourceReferenceSha256": source.source_reference_sha256,
                    "sourceFootprintSha256": source.source_footprint_sha256,
                    "sourceGeometrySha256": source.source_geometry_sha256,
                    "qualificationStatus": "REJECTED",
                    "rejectionCode": str(exc),
                }
            item["featureFingerprint"] = _canonical(
                {
                    "planId": PLAN_ID,
                    "scope": scope,
                    "placeId": item["placeId"],
                    "parentSourcePlaceCode": item["parentSourcePlaceCode"],
                    "parentAdministrativeAreaId": item.get("parentAdministrativeAreaId"),
                    "sourceGeometrySha256": item["sourceGeometrySha256"],
                    "geometrySha256": item.get("geometrySha256"),
                    "qualificationStatus": item["qualificationStatus"],
                    "rejectionCode": item.get("rejectionCode"),
                }
            )
            candidates.append(item)

        candidates.sort(key=lambda item: str(item["placeId"]))
        if not sources:
            raise RuntimeError("TOWN source selection is empty")
        first = sources[0]
        body = {
            "databaseName": self.database_name,
            "environmentName": self.environment_name,
            "repositoryRevision": self.repository_revision,
            "effectiveDate": self.effective_date,
            "sourceDatasetId": first.dataset_id,
            "sourceDatasetVersion": first.dataset_version,
            "sourceDatasetSha256": first.source_dataset_sha256,
            "sourceReferenceSha256": first.source_reference_sha256,
            "sourceFootprintSha256": first.source_footprint_sha256,
            "towns": tuple(candidates),
            **scope,
        }
        body["fingerprint"] = _canonical(
            {"planId": PLAN_ID, "planVersion": PLAN_VERSION, **body}
        )
        return IncrementalTownPlan(body)

    def preview_municipality(self, municipality_id: str) -> IncrementalTownPlan:
        parent = self._published_municipality(municipality_id)
        sources = load_town_sources(
            self.footprint_path,
            self.reference_path,
            self.summary_path,
        )
        selected = tuple(
            source
            for source in sources
            if source.parent_source_place_code == parent["sourceRecordId"]
        )
        # Bundle19A's governed contract is five towns per municipality. This is
        # a source-integrity assertion, not a publication completeness gate.
        if len(selected) != 5:
            raise RuntimeError(
                "LOCKED_TOWN_SOURCE_PARENT_GROUP_MUST_CONTAIN_FIVE_FEATURES"
            )
        return self._build_plan(
            selected,
            scope={
                "scopeType": "MUNICIPALITY",
                "municipalityId": parent["municipalityId"],
                "municipalityName": parent["canonicalName"],
                "municipalitySourceRecordId": parent["sourceRecordId"],
                "municipalityGeometryId": parent["geometryId"],
                "municipalityGeometrySha256": parent["geometrySha256"],
                "parentRegionId": parent["parentRegionId"],
            },
        )

    def preview_national(self) -> IncrementalTownPlan:
        """Backward-compatible read-only aggregate preview; not the writer gate."""
        sources = load_town_sources(
            self.footprint_path,
            self.reference_path,
            self.summary_path,
        )
        return self._build_plan(sources, scope={"scopeType": "NATIONAL_READ_ONLY"})

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
                FROM geography.nngla_town_publication
                WHERE place_id=%s
                  AND publication_id=%s
                  AND publication_status='PUBLISHED'
                """,
                (item["placeId"], item["publicationId"]),
            )
            return cursor.fetchone() is not None

    def _write_receipt(self, item, *, submitter, approver, status, inserted, reused, failed, publication_ready, detail):
        now = datetime.now(timezone.utc)
        fingerprint = str(item["featureFingerprint"])
        eid = _execution_id(fingerprint)
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
                    eid, PLAN_ID, PLAN_VERSION, fingerprint, self.environment_name,
                    self.repository_revision, item["sourceDatasetSha256"], submitter, approver,
                    inserted, reused, failed, status, now, now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO geography.nngla_execution_item(
                  execution_id,source_record_id,canonical_id,outcome,publication_ready,detail
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    eid, item["sourcePlaceCode"], item["placeId"], status, publication_ready,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )

    def _persist_qualified(self, item, submitter, approver) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            if not self._feature_public_exists(item):
                raise RuntimeError("TOWN execution receipt exists but public feature is absent")
            return "REUSED"
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT town_footprint_id,geometry_sha256
                FROM geography.nngla_town_settlement_footprint_record
                WHERE place_id=%s AND effective_to IS NULL AND qualification_status='QUALIFIED'
                """,
                (item["placeId"],),
            )
            current = cursor.fetchone()
            inserted = False
            if current is None:
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
                        item["geometrySha256"], self.effective_date,
                    ),
                )
                inserted = True
            elif (str(current[0]), str(current[1])) != (str(item["footprintId"]), str(item["geometrySha256"])):
                raise RuntimeError("current TOWN footprint differs from approved feature plan")

            cursor.execute(
                """
                INSERT INTO geography.nngla_town_footprint_qualification(
                  qualification_id,place_id,town_footprint_id,geometry_sha256,is_valid,is_non_empty,
                  is_polygonal,identity_parentage_match,source_contract_match,qualification_status,
                  policy_version,qualified_at
                ) VALUES (%s,%s,%s,%s,true,true,true,true,true,'QUALIFIED',1,%s)
                ON CONFLICT (qualification_id) DO NOTHING
                """,
                (item["qualificationId"], item["placeId"], item["footprintId"], item["geometrySha256"], datetime.now(timezone.utc)),
            )
            cursor.execute(
                """
                SELECT publication_id FROM geography.nngla_town_publication
                WHERE place_id=%s AND publication_status='PUBLISHED'
                """,
                (item["placeId"],),
            )
            current_pub = cursor.fetchone()
            if current_pub is None:
                cursor.execute(
                    """
                    INSERT INTO geography.nngla_town_publication(
                      publication_id,place_id,town_footprint_id,qualification_id,publication_status,published_at
                    ) VALUES (%s,%s,%s,%s,'PUBLISHED',%s)
                    """,
                    (item["publicationId"], item["placeId"], item["footprintId"], item["qualificationId"], datetime.now(timezone.utc)),
                )
                inserted = True
            elif str(current_pub[0]) != str(item["publicationId"]):
                raise RuntimeError("current TOWN publication differs from approved feature plan")

        self._write_receipt(
            item, submitter=submitter, approver=approver,
            status="APPLIED" if inserted else "REUSED",
            inserted=1 if inserted else 0, reused=0 if inserted else 1, failed=0,
            publication_ready=True,
            detail={
                "place_id": item["placeId"],
                "parent_administrative_area_id": item["parentAdministrativeAreaId"],
                "town_footprint_id": item["footprintId"],
                "qualification_id": item["qualificationId"],
                "publication_id": item["publicationId"],
                "geometry_sha256": item["geometrySha256"],
                "source_reference_sha256": item["sourceReferenceSha256"],
                "source_footprint_sha256": item["sourceFootprintSha256"],
            },
        )
        return "APPLIED" if inserted else "REUSED"

    def _persist_rejected(self, item, submitter, approver) -> str:
        if self._receipt_exists(str(item["featureFingerprint"])):
            return "REUSED"
        self._write_receipt(
            item, submitter=submitter, approver=approver, status="FAILED",
            inserted=0, reused=0, failed=1, publication_ready=False,
            detail={
                "place_id": item["placeId"],
                "parent_source_place_code": item["parentSourcePlaceCode"],
                "parent_administrative_area_id": item.get("parentAdministrativeAreaId"),
                "rejection_code": item.get("rejectionCode"),
                "source_geometry_sha256": item["sourceGeometrySha256"],
            },
        )
        return "FAILED"

    def _execute_plan(
        self,
        plan: IncrementalTownPlan,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ) -> IncrementalTownExecutionResult:
        submitter = str(submitter_actor_id).strip()
        approver = str(approver_actor_id).strip()
        if not submitter or not approver:
            raise ValueError("submitter and approver actor IDs are required")
        if submitter == approver:
            raise ValueError("submitter and approver must be different actors")
        if plan.fingerprint != str(approved_fingerprint).strip():
            raise RuntimeError("approved fingerprint does not match fresh TOWN incremental plan")
        if plan.confirmation_token != str(confirmation).strip():
            raise RuntimeError("confirmation token does not match fresh TOWN incremental plan")

        self.connection.commit()
        inserted = reused = failed = 0
        outcomes: list[dict[str, object]] = []
        for item in plan.payload["towns"]:
            try:
                with self.connection.transaction():
                    if item["qualificationStatus"] == "QUALIFIED":
                        outcome = self._persist_qualified(item, submitter, approver)
                        if outcome == "APPLIED":
                            inserted += 1
                        else:
                            reused += 1
                    else:
                        outcome = self._persist_rejected(item, submitter, approver)
                        if outcome == "FAILED":
                            failed += 1
                        else:
                            reused += 1
                outcomes.append({"placeId": item["placeId"], "outcome": outcome})
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
                                "place_id": item["placeId"],
                                "rejection_code": "PERSISTENCE_ERROR",
                                "error": str(exc),
                                "approved_feature_fingerprint": item["featureFingerprint"],
                            },
                        )
                except Exception as receipt_exc:
                    receipt_error = str(receipt_exc)
                outcome = {"placeId": item["placeId"], "outcome": "FAILED", "error": str(exc)}
                if receipt_error:
                    outcome["receiptError"] = receipt_error
                outcomes.append(outcome)

        status = (
            "PARTIAL" if failed and (inserted or reused)
            else "FAILED" if failed
            else "APPLIED" if inserted
            else "REUSED"
        )
        return IncrementalTownExecutionResult(
            {
                "planId": PLAN_ID,
                "planVersion": PLAN_VERSION,
                "fingerprint": plan.fingerprint,
                "scopeType": plan.payload.get("scopeType"),
                "municipalityId": plan.payload.get("municipalityId"),
                "databaseName": plan.database_name,
                "environmentName": self.environment_name,
                "repositoryRevision": self.repository_revision,
                "status": status,
                "insertedCount": inserted,
                "reusedCount": reused,
                "failedCount": failed,
                "outcomes": outcomes,
            }
        )

    def execute_municipality(
        self,
        municipality_id: str,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ) -> IncrementalTownExecutionResult:
        plan = self.preview_municipality(municipality_id)
        return self._execute_plan(
            plan,
            approved_fingerprint=approved_fingerprint,
            confirmation=confirmation,
            submitter_actor_id=submitter_actor_id,
            approver_actor_id=approver_actor_id,
        )

    def execute_national(
        self,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ) -> IncrementalTownExecutionResult:
        """Fail closed for stale callers; sequence 29 writes per municipality."""
        raise RuntimeError(
            "NATIONAL_TOWN_ATOMIC_EXECUTION_DISABLED_BY_SEQUENCE_29; "
            "use execute_municipality"
        )

