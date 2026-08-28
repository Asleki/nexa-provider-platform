"""Delivery 3 R1 orchestration: exact qualification then explicit CITY adoption."""
from __future__ import annotations

from .city_qualification import PostgreSQLCityEvidenceResolver, PostgreSQLCityFeatureQualifier
from .contracts import (
    CandidateSourceMode,
    CityAuthorityAdoptionRequest,
    CityQualificationReceipt,
    PrecisionMode,
    PrecisionPolicy,
)


class AuthorityAdoptionError(RuntimeError):
    pass


def precision_policy_from_receipt(receipt: CityQualificationReceipt) -> PrecisionPolicy:
    return PrecisionPolicy(
        policy_id=receipt.precision_policy_id,
        mode=receipt.precision_mode,
        grid_size_degrees=receipt.precision_grid_size_degrees,
        evidence_reference=receipt.precision_evidence_reference,
        policy_sha256=receipt.precision_policy_sha256,
    )


def request_from_qualification(
    receipt: CityQualificationReceipt,
    *,
    effective_on: str,
    submitter_actor_id: str,
    approver_actor_id: str,
    decision_reference: str,
    rationale: str,
) -> CityAuthorityAdoptionRequest:
    if not receipt.feature_qualified:
        raise AuthorityAdoptionError("CITY authority adoption requires CITY_READY_FOR_AUTHORITY")
    return CityAuthorityAdoptionRequest(
        qualification_id=receipt.qualification_id,
        qualification_sha256=receipt.qualification_sha256,
        city_administrative_area_id=receipt.city_administrative_area_id,
        candidate_id=receipt.candidate_id,
        candidate_geometry_sha256=receipt.evaluated_candidate_geometry_sha256,
        candidate_source_mode=receipt.candidate_source_mode,
        validation_parent_id=receipt.validation_parent_id,
        parent_evidence_id=receipt.parent_evidence_id,
        parent_geometry_sha256=receipt.evaluated_parent_geometry_sha256,
        parent_qualification_reference=receipt.parent_qualification_reference,
        peer_evidence_digest=receipt.peer_evidence_digest,
        precision_policy_id=receipt.precision_policy_id,
        precision_policy_sha256=receipt.precision_policy_sha256,
        effective_on=effective_on,
        qualifier_actor_id=receipt.qualifier_actor_id,
        submitter_actor_id=submitter_actor_id,
        approver_actor_id=approver_actor_id,
        decision_reference=decision_reference,
        rationale=rationale,
    )


class GovernedAdministrativeAuthorityService:
    def __init__(self, connection, repository) -> None:
        self.connection = connection
        self.repository = repository
        self.qualifier = PostgreSQLCityFeatureQualifier(connection)
        self.resolver = PostgreSQLCityEvidenceResolver(connection)

    def adopt_city(
        self,
        technical_receipt: CityQualificationReceipt,
        *,
        effective_on: str,
        submitter_actor_id: str,
        approver_actor_id: str,
        decision_reference: str,
        rationale: str,
    ):
        policy = precision_policy_from_receipt(technical_receipt)
        rerun = self.qualifier.qualify(
            technical_receipt.city_administrative_area_id,
            qualifier_actor_id=technical_receipt.qualifier_actor_id,
            candidate_source_mode=technical_receipt.candidate_source_mode,
            fabric_run_id=technical_receipt.fabric_run_id,
            precision_policy=policy,
            enforce_read_only_transaction=False,
        )
        if rerun.qualification_sha256 != technical_receipt.qualification_sha256:
            raise AuthorityAdoptionError("CITY qualification evidence became stale before adoption")
        if not rerun.feature_qualified:
            raise AuthorityAdoptionError("CITY no longer passes exact qualification")
        candidate = (
            self.resolver.frozen_candidate(rerun.city_administrative_area_id)
            if rerun.candidate_source_mode is CandidateSourceMode.FROZEN_SOURCE_REUSE
            else self.resolver.delivery2_candidate(rerun.city_administrative_area_id, rerun.fabric_run_id)
        )
        request = request_from_qualification(
            rerun,
            effective_on=effective_on,
            submitter_actor_id=submitter_actor_id,
            approver_actor_id=approver_actor_id,
            decision_reference=decision_reference,
            rationale=rationale,
        )
        return self.repository.adopt_city(
            rerun,
            request,
            raw_candidate_wkb_hex=candidate.geometry_wkb_hex,
            precision_policy=policy,
        )


__all__ = [
    "AuthorityAdoptionError", "GovernedAdministrativeAuthorityService",
    "precision_policy_from_receipt", "request_from_qualification",
]
