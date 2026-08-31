"""Governed read-only preview and per-REGION MUNICIPALITY execution."""
from __future__ import annotations

from dataclasses import asdict

from .contracts import MunicipalityRegionPlan
from .planning import (
    canonical_sha256,
    fingerprint_payload,
    member_set_payload,
    municipality_geometry_id,
    municipality_publication_id,
    normalize_effective_date,
    partition_qualification_id,
)
from .source import sources_for_region_source_record


class GovernedMunicipalityRealizationService:
    def __init__(
        self,
        repository,
        postgis,
        *,
        repository_revision: str,
        effective_date: str | None = None,
    ) -> None:
        if repository is None or postgis is None:
            raise TypeError("repository and postgis are required")
        if not str(repository_revision).strip():
            raise ValueError("repository_revision is required")
        self.repository = repository
        self.postgis = postgis
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = normalize_effective_date(effective_date)

    def preview_region(self, region_id: str) -> MunicipalityRegionPlan:
        region = self.postgis.load_region(str(region_id).strip())
        city = self.postgis.load_city(region.region_id)
        sources = sources_for_region_source_record(region.source_record_id)

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
                raise RuntimeError(
                    "live MUNICIPALITY identity does not match locked Bundle19B evidence"
                )
            if identity.parent_source_record_id != region.source_record_id:
                raise RuntimeError("MUNICIPALITY parent_source_record_id does not bind exact REGION")
            if identity.region_code != region.region_code:
                raise RuntimeError("MUNICIPALITY region_code does not match exact REGION")

            value = self.postgis.realize(source, region, city)
            realized.append(value)
            items.append(
                {
                    "municipalityId": source.administrative_area_id,
                    "canonicalName": source.canonical_name,
                    "sourceRecordId": source.source_record_id,
                    "sourceDatasetId": source.source_dataset_id,
                    "sourceDatasetVersion": source.source_dataset_version,
                    "sourcePathReference": source.source_path_reference,
                    "sourceDatasetSha256": source.source_dataset_sha256,
                    "sourceGeometrySha256": source.source_geometry_sha256,
                    "realizationMethod": value.realization_method,
                    "geometryId": municipality_geometry_id(source.administrative_area_id),
                    "publicationId": municipality_publication_id(source.administrative_area_id),
                    "geometryTypeCode": value.geometry_type_code,
                    "geometry": value.geometry,
                    "geometrySha256": value.geometry_sha256,
                    "labelPoint": value.label_point,
                    "areaM2": value.area_m2,
                    "areaKm2": value.area_km2,
                    "perimeterM": value.perimeter_m,
                    "perimeterKm": value.perimeter_km,
                    "sourceAreaM2": value.source_area_m2,
                    "sourceOutsideRegionM2": value.source_outside_region_m2,
                    "sourceCityOverlapM2": value.source_city_overlap_m2,
                }
            )

        partition = asdict(
            self.postgis.qualify_partition(region, city, tuple(realized))
        )
        members = member_set_payload(items)
        member_set_sha = canonical_sha256(members)
        fingerprint = fingerprint_payload(
            {
                "databaseName": self.repository.database_name,
                "environmentName": self.repository.environment_name,
                "repositoryRevision": self.repository_revision,
                "effectiveDate": self.effective_date,
                "parentRegionId": region.region_id,
                "parentRegionGeometryId": region.region_geometry_id,
                "parentRegionGeometrySha256": region.geometry_sha256,
                "cityId": city.city_id,
                "cityGeometryId": city.city_geometry_id,
                "cityGeometrySha256": city.geometry_sha256,
                "cityPublicationId": city.publication_id,
                "municipalityGeometrySetSha256": member_set_sha,
                "municipalities": items,
                "partition": partition,
            }
        )
        return MunicipalityRegionPlan(
            database_name=self.repository.database_name,
            environment_name=self.repository.environment_name,
            repository_revision=self.repository_revision,
            effective_date=self.effective_date,
            parent_region_id=region.region_id,
            parent_region_name=region.canonical_name,
            region_code=region.region_code,
            parent_region_geometry_id=region.region_geometry_id,
            parent_region_geometry_sha256=region.geometry_sha256,
            city_id=city.city_id,
            city_geometry_id=city.city_geometry_id,
            city_geometry_sha256=city.geometry_sha256,
            city_publication_id=city.publication_id,
            partition_qualification_id=partition_qualification_id(region.region_id),
            municipality_geometry_set_sha256=member_set_sha,
            municipality_member_set=members,
            municipalities=tuple(items),
            partition=partition,
            fingerprint=fingerprint,
        )

    def execute_region(
        self,
        region_id: str,
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
            plan = self.preview_region(region_id)
            if plan.fingerprint != str(approved_fingerprint).strip():
                raise RuntimeError("approved fingerprint does not match fresh MUNICIPALITY plan")
            if plan.confirmation_token != str(confirmation).strip():
                raise RuntimeError("confirmation token does not match fresh MUNICIPALITY plan")

            replay = self.repository.replay(plan.fingerprint)
            if replay is not None:
                self.repository.verify_public(plan)
                return replay

            current_count = self.repository.current_publication_count(
                plan.parent_region_id
            )
            if current_count == 3:
                self.repository.verify_public(plan)
                return self.repository.persist_execution(
                    plan,
                    submitter_actor_id=submitter,
                    approver_actor_id=approver,
                    status="REUSED",
                    inserted_count=0,
                    reused_count=3,
                )
            if current_count != 0:
                raise RuntimeError(
                    "partial current MUNICIPALITY publication exists; automatic repair prohibited"
                )
            if plan.partition.get("partition_status") != "COMPLETE":
                raise RuntimeError("MUNICIPALITY partition is not COMPLETE")

            self.repository.insert_region_fabric(plan)
            self.repository.verify_public(plan)
            return self.repository.persist_execution(
                plan,
                submitter_actor_id=submitter,
                approver_actor_id=approver,
                status="APPLIED",
                inserted_count=3,
                reused_count=0,
            )
