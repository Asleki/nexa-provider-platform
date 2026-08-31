"""Governed national preview/execution for TOWN settlement-footprint publication."""
from __future__ import annotations

from .contracts import TownNationalPlan
from .planning import (
    build_member_set,
    canonical_sha256,
    fingerprint_payload,
    normalize_effective_date,
    publication_id,
    qualification_id,
    qualify_source,
    town_footprint_id,
)
from .source import load_town_sources


class GovernedTownFootprintRealizationService:
    def __init__(
        self,
        repository,
        postgis,
        *,
        footprint_path,
        reference_path,
        summary_path,
        repository_revision: str,
        effective_date: str | None = None,
    ) -> None:
        if repository is None or postgis is None:
            raise TypeError("repository and postgis are required")
        if not str(repository_revision).strip():
            raise ValueError("repository_revision is required")
        self.repository = repository
        self.postgis = postgis
        self.footprint_path = footprint_path
        self.reference_path = reference_path
        self.summary_path = summary_path
        self.repository_revision = str(repository_revision).strip()
        self.effective_date = normalize_effective_date(effective_date)

    def preview_national(self) -> TownNationalPlan:
        sources = load_town_sources(self.footprint_path, self.reference_path, self.summary_path)
        items = []
        for source in sources:
            identity = self.postgis.load_identity(source.place_id)
            qualify_source(source, identity)
            value = self.postgis.realize(source, identity)
            items.append(
                {
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
                    "geometryTypeCode": value.geometry_type_code,
                    "geometry": value.geometry,
                    "geometrySha256": value.geometry_sha256,
                    "labelPoint": value.label_point,
                    "areaM2": value.area_m2,
                    "areaKm2": value.area_km2,
                    "perimeterM": value.perimeter_m,
                    "perimeterKm": value.perimeter_km,
                    "coveredByParentMunicipality": value.covered_by_parent_municipality,
                }
            )

        if len(items) != 120 or not all(item["coveredByParentMunicipality"] for item in items):
            raise RuntimeError("TOWN national realization is not publication-ready")
        members = build_member_set(items)
        member_sha = canonical_sha256(members)
        first = sources[0]
        fingerprint = fingerprint_payload(
            {
                "databaseName": self.repository.database_name,
                "environmentName": self.repository.environment_name,
                "repositoryRevision": self.repository_revision,
                "effectiveDate": self.effective_date,
                "sourceDatasetId": first.dataset_id,
                "sourceDatasetVersion": first.dataset_version,
                "sourceDatasetSha256": first.source_dataset_sha256,
                "sourceReferenceSha256": first.source_reference_sha256,
                "sourceFootprintSha256": first.source_footprint_sha256,
                "townMemberSetSha256": member_sha,
                "towns": items,
            }
        )
        return TownNationalPlan(
            database_name=self.repository.database_name,
            environment_name=self.repository.environment_name,
            repository_revision=self.repository_revision,
            effective_date=self.effective_date,
            source_dataset_id=first.dataset_id,
            source_dataset_version=first.dataset_version,
            source_dataset_sha256=first.source_dataset_sha256,
            source_reference_sha256=first.source_reference_sha256,
            source_footprint_sha256=first.source_footprint_sha256,
            town_member_set_sha256=member_sha,
            town_member_set=members,
            towns=tuple(items),
            fingerprint=fingerprint,
        )

    def execute_national(
        self,
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
            plan = self.preview_national()
            if plan.fingerprint != str(approved_fingerprint).strip():
                raise RuntimeError("approved fingerprint does not match fresh TOWN plan")
            if plan.confirmation_token != str(confirmation).strip():
                raise RuntimeError("confirmation token does not match fresh TOWN plan")

            replay = self.repository.replay(plan.fingerprint)
            if replay is not None:
                self.repository.verify_public(plan)
                return replay

            current_count = self.repository.current_publication_count()
            if current_count == 120:
                self.repository.verify_public(plan)
                return self.repository.persist_execution(
                    plan,
                    submitter_actor_id=submitter,
                    approver_actor_id=approver,
                    status="REUSED",
                    inserted_count=0,
                    reused_count=120,
                )
            if current_count != 0:
                raise RuntimeError("partial current TOWN publication exists; automatic repair prohibited")

            self.repository.insert_national_set(plan)
            self.repository.verify_public(plan)
            return self.repository.persist_execution(
                plan,
                submitter_actor_id=submitter,
                approver_actor_id=approver,
                status="APPLIED",
                inserted_count=120,
                reused_count=0,
            )


TownFootprintRealizationService = GovernedTownFootprintRealizationService
