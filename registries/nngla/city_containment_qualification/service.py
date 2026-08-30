"""Governed orchestration for deterministic CITY parent-containment qualification."""
from __future__ import annotations

from typing import Callable

from registries.nngla.city_realization.contracts import (
    OFFICIAL_CITY_SET,
    REALIZATION_VERSION,
)
from registries.nngla.city_realization.planning import (
    city_geometry_id,
    city_publication_id,
    normalize_effective_date,
)
from registries.nngla.city_realization.source import load_city_source

from .contracts import (
    ABSOLUTE_RESIDUE_MAX_M2,
    QUALIFICATION_POLICY_VERSION,
    RATIO_RESIDUE_MAX,
    CityContainmentQualificationPlan,
    QualificationStatus,
)
from .planning import qualification_fingerprint, qualification_id


class GovernedCityContainmentQualificationService:
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

    def _qualification_matches(self, current_q, plan_core) -> bool:
        if current_q is None:
            return False
        expected = (
            plan_core["qualification_id"],
            plan_core["city_geometry_id"],
            plan_core["geometry_sha256"],
            plan_core["parent_region_id"],
            plan_core["parent_region_geometry_id"],
            plan_core["parent_region_geometry_sha256"],
            plan_core["realization_method"],
            REALIZATION_VERSION,
            plan_core["qualification_status"],
            plan_core["qualification_basis_code"],
            QUALIFICATION_POLICY_VERSION,
            ABSOLUTE_RESIDUE_MAX_M2,
            RATIO_RESIDUE_MAX,
            self.effective_date,
        )
        actual = (
            str(current_q[0]), str(current_q[1]), str(current_q[2]),
            str(current_q[3]), str(current_q[4]), str(current_q[5]),
            str(current_q[6]), int(current_q[7]), str(current_q[8]),
            str(current_q[9]), int(current_q[10]), float(current_q[11]),
            float(current_q[12]), str(current_q[13]),
        )
        return actual == expected

    def _planned_action(self, *, current, current_q, plan_core) -> str:
        qualified = plan_core["qualification_status"] == QualificationStatus.QUALIFIED.value
        qualification_matches = self._qualification_matches(current_q, plan_core)
        if current is None:
            if current_q is None:
                return "INSERT_AND_PUBLISH" if qualified else "QUALIFY_ONLY"
            if not qualification_matches:
                raise RuntimeError("current CITY containment qualification differs from deterministic plan")
            if qualified:
                raise RuntimeError("qualified containment evidence exists without corresponding CITY authority")
            return "REUSE"

        expected = (
            plan_core["city_geometry_id"],
            plan_core["geometry_sha256"],
            plan_core["parent_region_id"],
            plan_core["parent_region_geometry_id"],
            plan_core["parent_region_geometry_sha256"],
            plan_core["realization_method"],
            REALIZATION_VERSION,
        )
        actual = (
            current.city_geometry_id,
            current.geometry_sha256,
            current.parent_region_id,
            current.parent_region_geometry_id,
            current.parent_region_geometry_sha256,
            current.realization_method,
            current.realization_version,
        )
        if actual != expected:
            raise RuntimeError(
                "current authoritative CITY geometry differs from deterministic containment plan; "
                "automatic supersession is prohibited"
            )
        if current.publication_id != plan_core["publication_id"] or current.publication_status != "PUBLISHED":
            raise RuntimeError("current CITY publication identity/status differs from containment plan")
        if not qualified:
            raise RuntimeError("existing published CITY failed current containment qualification")
        if current_q is None:
            return "ATTEST_EXISTING"
        if not qualification_matches:
            raise RuntimeError("current CITY containment qualification differs from deterministic plan")
        return "REUSE"

    def preview(self, city_id: str) -> CityContainmentQualificationPlan:
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

        evidence = self.postgis.evaluate(source, parent)
        gid = city_geometry_id(normalized, REALIZATION_VERSION)
        pid = city_publication_id(normalized, REALIZATION_VERSION)
        qid = qualification_id(
            city_id=normalized,
            city_geometry_id=gid,
            parent_region_geometry_id=parent.region_geometry_id,
            qualification_policy_version=QUALIFICATION_POLICY_VERSION,
        )

        core = {
            "city_geometry_id": gid,
            "publication_id": pid,
            "parent_region_id": parent.region_id,
            "parent_region_geometry_id": parent.region_geometry_id,
            "parent_region_geometry_sha256": parent.geometry_sha256,
            "realization_method": evidence.realization_method,
            "geometry_sha256": evidence.geometry_sha256,
            "qualification_status": evidence.qualification_status.value,
            "qualification_id": qid,
            "qualification_basis_code": evidence.qualification_basis.value,
        }
        current = self.repository.current_city_authority(normalized)
        current_q = self.repository.current_qualification(normalized)
        action = self._planned_action(current=current, current_q=current_q, plan_core=core)

        fingerprint = qualification_fingerprint(
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
                "realizationMethod": evidence.realization_method,
                "realizationVersion": REALIZATION_VERSION,
                "cityGeometryId": gid,
                "publicationId": pid,
                "geometryTypeCode": evidence.normalized_geometry_type,
                "geometrySha256": evidence.geometry_sha256,
                "labelPoint": evidence.label_point,
                "sourceValid": evidence.source_valid,
                "sourceNonEmpty": evidence.source_non_empty,
                "sourceStrictCovered": evidence.source_strict_covered,
                "sourceAreaM2": evidence.source_area_m2,
                "sourceOutsideParentM2": evidence.source_outside_parent_m2,
                "sourceOutsideParentRatio": evidence.source_outside_parent_ratio,
                "normalizedValid": evidence.normalized_valid,
                "normalizedNonEmpty": evidence.normalized_non_empty,
                "normalizedStrictCovered": evidence.normalized_strict_covered,
                "normalizedAreaM2": evidence.normalized_area_m2,
                "normalizedOutsideParentM2": evidence.normalized_outside_parent_m2,
                "normalizedOutsideParentRatio": evidence.normalized_outside_parent_ratio,
                "perimeterM": evidence.perimeter_m,
                "areaRemovedM2": evidence.area_removed_m2,
                "areaRemovedRatio": evidence.area_removed_ratio,
                "qualificationId": qid,
                "qualificationStatus": evidence.qualification_status.value,
                "qualificationBasisCode": evidence.qualification_basis.value,
                "qualificationPolicyVersion": QUALIFICATION_POLICY_VERSION,
                "absoluteResidueMaxM2": ABSOLUTE_RESIDUE_MAX_M2,
                "ratioResidueMax": RATIO_RESIDUE_MAX,
            }
        )

        return CityContainmentQualificationPlan(
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
            realization_method=evidence.realization_method,
            realization_version=REALIZATION_VERSION,
            city_geometry_id=gid,
            publication_id=pid,
            planned_action=action,
            geometry_type_code=evidence.normalized_geometry_type,
            crs_code="NG-CRS-EPSG4326",
            geometry=evidence.geometry,
            geometry_sha256=evidence.geometry_sha256,
            label_point=evidence.label_point,
            source_valid=evidence.source_valid,
            source_non_empty=evidence.source_non_empty,
            source_geometry_type=evidence.source_geometry_type,
            source_strict_covered=evidence.source_strict_covered,
            source_area_m2=evidence.source_area_m2,
            source_outside_parent_m2=evidence.source_outside_parent_m2,
            source_outside_parent_ratio=evidence.source_outside_parent_ratio,
            normalized_valid=evidence.normalized_valid,
            normalized_non_empty=evidence.normalized_non_empty,
            normalized_geometry_type=evidence.normalized_geometry_type,
            normalized_strict_covered=evidence.normalized_strict_covered,
            normalized_outside_parent_m2=evidence.normalized_outside_parent_m2,
            normalized_outside_parent_ratio=evidence.normalized_outside_parent_ratio,
            area_m2=evidence.normalized_area_m2,
            area_km2=evidence.normalized_area_m2 / 1_000_000.0,
            perimeter_m=evidence.perimeter_m,
            perimeter_km=evidence.perimeter_m / 1_000.0,
            area_removed_m2=evidence.area_removed_m2,
            area_removed_ratio=evidence.area_removed_ratio,
            label_point_covered=evidence.label_point_covered,
            qualification_id=qid,
            qualification_status=evidence.qualification_status.value,
            qualification_basis_code=evidence.qualification_basis.value,
            qualification_policy_version=QUALIFICATION_POLICY_VERSION,
            absolute_residue_max_m2=ABSOLUTE_RESIDUE_MAX_M2,
            ratio_residue_max=RATIO_RESIDUE_MAX,
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
                raise RuntimeError("approved fingerprint does not match fresh containment plan")
            if fresh.confirmation_token != str(confirmation).strip():
                raise RuntimeError("confirmation token does not match fresh containment plan")

            replay = self.repository.replay(fresh.fingerprint)
            if replay is not None:
                self.repository.verify_qualification(fresh)
                if fresh.public_ready:
                    self.repository.verify_public(fresh)
                return replay

            inserted_geometry = 0
            inserted_qualification = 0
            inserted_publication = 0
            reused_geometry = 0

            if fresh.planned_action == "INSERT_AND_PUBLISH":
                self.repository.insert_qualification(fresh)
                inserted_qualification = 1
                self.repository.insert_geometry(fresh)
                inserted_geometry = 1
                self.repository.insert_publication(fresh)
                inserted_publication = 1
                status = "APPLIED"
            elif fresh.planned_action == "QUALIFY_ONLY":
                self.repository.insert_qualification(fresh)
                inserted_qualification = 1
                status = "APPLIED"
            elif fresh.planned_action == "ATTEST_EXISTING":
                self.repository.insert_qualification(fresh)
                inserted_qualification = 1
                reused_geometry = 1
                status = "APPLIED"
            elif fresh.planned_action == "REUSE":
                reused_geometry = 1
                status = "REUSED"
            else:
                raise RuntimeError("unsupported CITY containment qualification action")

            self.repository.verify_qualification(fresh)
            if fresh.public_ready:
                self.repository.verify_public(fresh)

            return self.repository.persist_execution(
                fresh,
                submitter_actor_id=submitter,
                approver_actor_id=approver,
                status=status,
                inserted_geometry_count=inserted_geometry,
                inserted_qualification_count=inserted_qualification,
                inserted_publication_count=inserted_publication,
                reused_geometry_count=reused_geometry,
            )
