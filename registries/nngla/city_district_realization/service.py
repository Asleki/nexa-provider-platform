"""Governed preview and per-CITY execution for CITY_DISTRICT publication."""
from __future__ import annotations

from .contracts import CityDistrictPlan
from .planning import (
    build_member_set,
    canonical_sha256,
    district_geometry_id,
    district_publication_id,
    fingerprint_payload,
    normalize_effective_date,
    partition_qualification_id,
    require_complete_partition,
)
from .source import sources_for_city_source_record


class GovernedCityDistrictRealizationService:
    def __init__(
        self,
        repository,
        postgis,
        *,
        source_path,
        repository_revision: str,
        effective_date: str | None = None,
    ) -> None:
        if repository is None or postgis is None:
            raise TypeError("repository and postgis are required")
        if not str(repository_revision).strip():
            raise ValueError("repository_revision is required")
        self.repository = repository
        self.postgis = postgis
        self.source_path = source_path
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = normalize_effective_date(effective_date)

    def preview_city(self, city_id: str) -> CityDistrictPlan:
        city = self.postgis.load_city(str(city_id).strip())
        sources = sources_for_city_source_record(self.source_path, city.source_record_id)
        realized = []
        items = []
        for source in sources:
            identity = self.postgis.load_identity(source.administrative_area_id)
            if (
                identity.canonical_name,
                identity.region_code,
                identity.source_record_id,
                identity.parent_source_record_id,
            ) != (
                source.canonical_name,
                source.region_code,
                source.source_record_id,
                source.parent_source_record_id,
            ):
                raise RuntimeError("live CITY_DISTRICT identity does not match locked Bundle19B evidence")
            if identity.parent_source_record_id != city.source_record_id:
                raise RuntimeError("CITY_DISTRICT parent source record does not bind exact CITY")
            if identity.region_code != city.region_code:
                raise RuntimeError("CITY_DISTRICT region code does not match parent CITY")
            value = self.postgis.realize(source, city)
            realized.append(value)
            items.append(
                {
                    "districtId": source.administrative_area_id,
                    "canonicalName": source.canonical_name,
                    "sourceRecordId": source.source_record_id,
                    "parentSourceRecordId": source.parent_source_record_id,
                    "sourceDatasetId": source.source_dataset_id,
                    "sourceDatasetVersion": source.source_dataset_version,
                    "sourcePathReference": source.source_path_reference,
                    "sourceDatasetSha256": source.source_dataset_sha256,
                    "sourceGeometrySha256": source.source_geometry_sha256,
                    "realizationMethod": value.realization_method,
                    "geometryId": district_geometry_id(source.administrative_area_id),
                    "publicationId": district_publication_id(source.administrative_area_id),
                    "geometryTypeCode": value.geometry_type_code,
                    "geometry": value.geometry,
                    "geometrySha256": value.geometry_sha256,
                    "labelPoint": value.label_point,
                    "areaM2": value.area_m2,
                    "areaKm2": value.area_km2,
                    "perimeterM": value.perimeter_m,
                    "perimeterKm": value.perimeter_km,
                }
            )

        partition = self.postgis.qualify_partition(city, tuple(realized))
        members = build_member_set(items)
        member_sha = canonical_sha256(members)
        fingerprint = fingerprint_payload(
            {
                "databaseName": self.repository.database_name,
                "environmentName": self.repository.environment_name,
                "repositoryRevision": self.repository_revision,
                "effectiveDate": self.effective_date,
                "parentCityId": city.city_id,
                "parentCitySourceRecordId": city.source_record_id,
                "parentCityGeometryId": city.city_geometry_id,
                "parentCityGeometrySha256": city.geometry_sha256,
                "districtGeometrySetSha256": member_sha,
                "districts": items,
                "partition": partition,
            }
        )
        return CityDistrictPlan(
            database_name=self.repository.database_name,
            environment_name=self.repository.environment_name,
            repository_revision=self.repository_revision,
            effective_date=self.effective_date,
            parent_city_id=city.city_id,
            parent_city_name=city.canonical_name,
            region_code=city.region_code,
            parent_city_source_record_id=city.source_record_id,
            parent_city_geometry_id=city.city_geometry_id,
            parent_city_geometry_sha256=city.geometry_sha256,
            partition_qualification_id=partition_qualification_id(city.city_id),
            district_geometry_set_sha256=member_sha,
            district_member_set=members,
            districts=tuple(items),
            partition=partition,
            fingerprint=fingerprint,
        )

    def execute_city(
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
            plan = self.preview_city(city_id)
            if plan.fingerprint != str(approved_fingerprint).strip():
                raise RuntimeError("approved fingerprint does not match fresh CITY_DISTRICT plan")
            if plan.confirmation_token != str(confirmation).strip():
                raise RuntimeError("confirmation token does not match fresh CITY_DISTRICT plan")
            require_complete_partition(plan.partition)

            replay = self.repository.replay(plan.fingerprint)
            if replay is not None:
                self.repository.verify_public(plan)
                return replay

            current_count = self.repository.current_publication_count(plan.parent_city_id)
            if current_count == 8:
                self.repository.verify_public(plan)
                return self.repository.persist_execution(
                    plan,
                    submitter_actor_id=submitter,
                    approver_actor_id=approver,
                    status="REUSED",
                    inserted_count=0,
                    reused_count=8,
                )
            if current_count != 0:
                raise RuntimeError("partial current CITY_DISTRICT publication exists; automatic repair prohibited")

            self.repository.insert_city_partition(plan)
            self.repository.verify_public(plan)
            return self.repository.persist_execution(
                plan,
                submitter_actor_id=submitter,
                approver_actor_id=approver,
                status="APPLIED",
                inserted_count=8,
                reused_count=0,
            )


# Backward-compatible name for imports created during the initial delivery.
CityDistrictRealizationService = GovernedCityDistrictRealizationService
