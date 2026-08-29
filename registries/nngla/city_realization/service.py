"""Governed preview/execute orchestration for P006.7.11.15.8."""
from __future__ import annotations

from typing import Callable

from .contracts import (
    CityRealizationPlan,
    OFFICIAL_CITY_SET,
    PlannedAction,
    REALIZATION_VERSION,
)
from .planning import (
    city_geometry_id,
    city_publication_id,
    fingerprint_payload,
    normalize_effective_date,
)
from .source import load_city_source


class GovernedCityRealizationService:
    def __init__(
        self,
        repository,
        postgis,
        *,
        repository_revision: str,
        effective_date: str | None = None,
        source_loader: Callable[[str], object] = load_city_source,
    ) -> None:
        if repository is None or postgis is None:
            raise TypeError("repository and postgis are required")
        revision = str(repository_revision).strip()
        if not revision:
            raise ValueError("repository_revision is required")
        self.repository = repository
        self.postgis = postgis
        self.repository_revision = revision
        self.effective_date = normalize_effective_date(effective_date)
        self.source_loader = source_loader

    def _planned_action(self, current, *, gid: str, pid: str, realized, parent) -> PlannedAction:
        if current is None:
            return PlannedAction.INSERT_AND_PUBLISH
        expected = (
            gid,
            realized.geometry_sha256,
            parent.region_id,
            parent.region_geometry_id,
            parent.geometry_sha256,
            realized.method.value,
            REALIZATION_VERSION,
            self.effective_date,
        )
        actual = (
            current.city_geometry_id,
            current.geometry_sha256,
            current.parent_region_id,
            current.parent_region_geometry_id,
            current.parent_region_geometry_sha256,
            current.realization_method,
            current.realization_version,
            current.effective_from,
        )
        if actual != expected:
            raise RuntimeError(
                "current authoritative CITY geometry differs from the planned initial realization; "
                "automatic supersession is prohibited"
            )
        if current.publication_id is None:
            return PlannedAction.PUBLISH_EXISTING
        if current.publication_id != pid or current.publication_status != "PUBLISHED":
            raise RuntimeError("current CITY publication identity/status differs from governed plan")
        return PlannedAction.REUSE

    def preview(self, city_id: str) -> CityRealizationPlan:
        normalized = str(city_id).strip()
        if normalized not in OFFICIAL_CITY_SET:
            raise ValueError(f"unsupported official NoveGeo CITY identity: {normalized}")
        source = self.source_loader(normalized)
        identity = self.postgis.load_city_identity(normalized)
        if (
            identity.administrative_area_id != source.administrative_area_id
            or identity.canonical_name != source.canonical_name
            or identity.region_code != source.region_code
        ):
            raise RuntimeError("live CITY identity does not match locked source evidence")
        parent = self.postgis.load_parent_region(identity.region_code)
        if parent.region_code != identity.region_code or parent.region_id == identity.administrative_area_id:
            raise RuntimeError("resolved parent REGION is inconsistent with CITY identity")
        realized = self.postgis.realize(source, parent)
        gid = city_geometry_id(normalized, REALIZATION_VERSION)
        pid = city_publication_id(normalized, REALIZATION_VERSION)
        current = self.repository.current_city_authority(normalized)
        action = self._planned_action(current, gid=gid, pid=pid, realized=realized, parent=parent)

        fingerprint = fingerprint_payload(
            {
                "databaseName": self.repository.database_name,
                "environmentName": self.repository.environment_name,
                "repositoryRevision": self.repository_revision,
                "effectiveDate": self.effective_date,
                "cityId": normalized,
                "canonicalName": identity.canonical_name,
                "regionCode": identity.region_code,
                "sourceRecordId": source.source_record_id,
                "boundaryCandidateId": source.boundary_candidate_id,
                "sourceDatasetId": source.source_dataset_id,
                "sourceDatasetVersion": source.source_dataset_version,
                "sourcePathReference": source.source_path_reference,
                "sourceDatasetSha256": source.source_dataset_sha256,
                "sourceGeometrySha256": source.source_geometry_sha256,
                "parentRegionId": parent.region_id,
                "parentRegionGeometryId": parent.region_geometry_id,
                "parentRegionGeometrySha256": parent.geometry_sha256,
                "realizationMethod": realized.method.value,
                "realizationVersion": REALIZATION_VERSION,
                "cityGeometryId": gid,
                "publicationId": pid,
                "geometryTypeCode": realized.geometry_type_code,
                "geometrySha256": realized.geometry_sha256,
                "labelPoint": realized.label_point,
                "sourceAreaM2": realized.source_area_m2,
                "sourceOutsideParentM2": realized.source_outside_parent_m2,
                "sourceOutsideParentRatio": realized.source_outside_parent_ratio,
                "areaM2": realized.final_area_m2,
                "perimeterM": realized.final_perimeter_m,
                "areaRemovedM2": realized.area_removed_m2,
                "areaRemovedRatio": realized.area_removed_ratio,
            }
        )
        return CityRealizationPlan(
            database_name=self.repository.database_name,
            environment_name=self.repository.environment_name,
            repository_revision=self.repository_revision,
            effective_date=self.effective_date,
            city_id=normalized,
            canonical_name=identity.canonical_name,
            region_code=identity.region_code,
            source_record_id=source.source_record_id,
            boundary_candidate_id=source.boundary_candidate_id,
            source_dataset_id=source.source_dataset_id,
            source_dataset_version=source.source_dataset_version,
            source_path_reference=source.source_path_reference,
            source_dataset_sha256=source.source_dataset_sha256,
            source_geometry_sha256=source.source_geometry_sha256,
            parent_region_id=parent.region_id,
            parent_region_name=parent.canonical_name,
            parent_region_geometry_id=parent.region_geometry_id,
            parent_region_geometry_sha256=parent.geometry_sha256,
            realization_method=realized.method.value,
            realization_version=REALIZATION_VERSION,
            city_geometry_id=gid,
            publication_id=pid,
            planned_action=action.value,
            geometry_type_code=realized.geometry_type_code,
            crs_code="NG-CRS-EPSG4326",
            geometry=realized.geometry,
            geometry_sha256=realized.geometry_sha256,
            label_point=realized.label_point,
            source_area_m2=realized.source_area_m2,
            source_outside_parent_m2=realized.source_outside_parent_m2,
            source_outside_parent_ratio=realized.source_outside_parent_ratio,
            area_m2=realized.final_area_m2,
            area_km2=realized.final_area_km2,
            perimeter_m=realized.final_perimeter_m,
            perimeter_km=realized.final_perimeter_km,
            area_removed_m2=realized.area_removed_m2,
            area_removed_ratio=realized.area_removed_ratio,
            fingerprint=fingerprint,
        )

    def execute(
        self,
        city_id: str,
        *,
        approved_fingerprint: str,
        confirmation: str,
        submitter_actor_id: str,
        approver_actor_id: str,
    ):
        submitter = str(submitter_actor_id).strip()
        approver = str(approver_actor_id).strip()
        if not submitter or not approver:
            raise ValueError("submitter and approver actor IDs are required")
        if submitter == approver:
            raise ValueError("submitter and approver must be different actors")
        with self.repository.transaction():
            fresh = self.preview(city_id)
            if fresh.fingerprint != str(approved_fingerprint).strip():
                raise RuntimeError("approved fingerprint does not match fresh realization plan")
            if fresh.confirmation_token != str(confirmation).strip():
                raise RuntimeError("confirmation token does not match fresh realization plan")
            replay = self.repository.replay(fresh.fingerprint)
            if replay is not None:
                self.repository.verify_public(fresh)
                return replay

            action = PlannedAction(fresh.planned_action)
            inserted = 0
            reused = 0
            if action is PlannedAction.INSERT_AND_PUBLISH:
                self.repository.insert_geometry(fresh)
                self.repository.insert_publication(fresh)
                inserted = 1
                status = "APPLIED"
            elif action is PlannedAction.PUBLISH_EXISTING:
                self.repository.insert_publication(fresh)
                reused = 1
                status = "APPLIED"
            elif action is PlannedAction.REUSE:
                reused = 1
                status = "REUSED"
            else:  # pragma: no cover - Enum is exhaustive
                raise RuntimeError("unsupported CITY realization action")

            self.repository.verify_public(fresh)
            return self.repository.persist_execution(
                fresh,
                submitter_actor_id=submitter,
                approver_actor_id=approver,
                status=status,
                inserted_geometry_count=inserted,
                reused_geometry_count=reused,
            )
