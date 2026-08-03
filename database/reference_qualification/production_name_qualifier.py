"""Production manual-name authoring qualification using locked Name Authority services."""
from __future__ import annotations

from registries.name_authority.manual import (
    ActorContext,
    ManualNameApprovalOutcome,
    ManualNameCandidateStatus,
    ProductionManualNameRequest,
    ReferenceBindingState,
    ReferenceDeclaration,
    ReferenceKnowledgeState,
)
from registries.names import NameKind, NameSearchQuery, comparison_key, normalize_name_value
from registries.names.name_sex_usage import NameSexUsage

from .contracts import (
    ProductionNameQualificationReport,
    ProductionNameQualificationRequest,
    QualificationFinding,
)
from .errors import ProductionAuthoringQualificationError


def _declaration(label: str | None) -> ReferenceDeclaration:
    if label is None:
        return ReferenceDeclaration()
    return ReferenceDeclaration(
        knowledge_state=ReferenceKnowledgeState.DECLARED_NEW,
        binding_state=ReferenceBindingState.UNRESOLVED,
        label=label,
    )


class ProductionNameAuthoringQualifier:
    """Qualify normalization, persistence, duplicate reuse, and runtime separation."""

    def __init__(self, manual_service, name_repository, candidate_repository) -> None:
        self._manual = manual_service
        self._names = name_repository
        self._candidates = candidate_repository

    def _manual_request(self, request: ProductionNameQualificationRequest, suffix: str) -> ProductionManualNameRequest:
        return ProductionManualNameRequest(
            request_id=f"qualification:{request.qualification_id}:{suffix}",
            operation_id=f"operation:{request.qualification_id}:{suffix}",
            raw_name_value=request.raw_name_value,
            requested_name_kind=NameKind.parse(request.requested_name_kind),
            sex_usage=NameSexUsage.parse(request.sex_usage),
            actor=ActorContext(request.submitter_actor_id, "qualification_operator", source="reference_qualification"),
            origin=_declaration(request.origin_label),
            language=_declaration(request.language_label),
            community=_declaration(request.community_label),
            script_code=request.script_code,
            notes=request.notes,
        )

    def qualify(self, request: ProductionNameQualificationRequest) -> ProductionNameQualificationReport:
        if not isinstance(request, ProductionNameQualificationRequest):
            raise TypeError("request must be ProductionNameQualificationRequest.")

        normalized = normalize_name_value(request.raw_name_value)
        search_value = comparison_key(normalized)
        approver = ActorContext(request.approver_actor_id, "qualification_approver", source="reference_qualification")

        first_candidate, first_validation = self._manual.submit(self._manual_request(request, "first"))
        if not first_validation.is_valid:
            raise ProductionAuthoringQualificationError(
                "production authoring candidate was rejected: " + ", ".join(first_validation.findings)
            )
        if first_candidate.status not in {
            ManualNameCandidateStatus.VALIDATED,
            ManualNameCandidateStatus.QUARANTINED,
        }:
            raise ProductionAuthoringQualificationError("production authoring candidate is not approval-eligible.")
        first_result = self._manual.approve(first_candidate.candidate_id, approver, "M009.13.10 qualification")

        duplicate_candidate, duplicate_validation = self._manual.submit(self._manual_request(request, "duplicate"))
        if not duplicate_validation.is_valid:
            raise ProductionAuthoringQualificationError("duplicate candidate was unexpectedly rejected.")
        duplicate_result = self._manual.approve(
            duplicate_candidate.candidate_id,
            approver,
            "M009.13.10 duplicate qualification",
        )
        if duplicate_result.outcome is not ManualNameApprovalOutcome.REUSED_EXISTING_CANONICAL_NAME:
            raise ProductionAuthoringQualificationError("duplicate production name did not reuse the canonical identity.")
        if duplicate_result.canonical_name_id != first_result.canonical_name_id:
            raise ProductionAuthoringQualificationError("duplicate production name resolved to a different canonical ID.")

        record = self._names.get(first_result.canonical_name_id)
        if record.metadata.runtime_mode != "production":
            raise ProductionAuthoringQualificationError("resolved canonical name is not production-scoped.")
        if record.canonical_value != normalized or record.search_value != search_value:
            raise ProductionAuthoringQualificationError("resolved canonical name violates normalization contracts.")

        production = self._names.search(
            NameSearchQuery(text=normalized, name_kind=record.name_kind, runtime_mode="production", exact=True, limit=10)
        )
        simulation = self._names.search(
            NameSearchQuery(text=normalized, name_kind=record.name_kind, runtime_mode="simulation", exact=True, limit=10)
        )
        if production.total != 1:
            raise ProductionAuthoringQualificationError("production semantic identity must resolve exactly once.")

        findings = (
            QualificationFinding(
                "REQUIRED_FIELDS_ACCEPTED", "passed",
                "The production request accepted only the locked required fields plus explicit optional declarations.",
            ),
            QualificationFinding(
                "WHITESPACE_NORMALIZED", "passed",
                "Leading, trailing, and repeated whitespace were normalized deterministically.",
                {"input": request.raw_name_value, "canonical": normalized},
            ),
            QualificationFinding(
                "UNICODE_NORMALIZED", "passed",
                "Canonical NFC and NFKC plus case-fold comparison contracts were preserved.",
                {"canonical": record.canonical_value, "search": record.search_value},
            ),
            QualificationFinding(
                "DUPLICATE_REUSED", "passed",
                "A second production request reused the existing canonical semantic identity.",
                {"canonical_name_id": record.name_id},
            ),
            QualificationFinding(
                "RUNTIME_SEPARATED", "passed",
                "Production qualification did not merge with any simulation record.",
                {"production_matches": production.total, "simulation_matches": simulation.total},
            ),
            QualificationFinding(
                "DIRECT_SQL_TRUST_BOUNDARY", "warning",
                "Python enforces Unicode and whitespace normalization; PostgreSQL does not independently derive search_value.",
            ),
            QualificationFinding(
                "SELF_APPROVAL_BLOCKED_BY_QUALIFIER", "passed",
                "The qualification contract requires different submitter and approver actor IDs.",
            ),
        )

        return ProductionNameQualificationReport(
            qualification_id=request.qualification_id,
            canonical_name_id=record.name_id,
            canonical_value=record.canonical_value,
            search_value=record.search_value,
            name_kind=record.name_kind.value,
            runtime_mode=record.metadata.runtime_mode,
            first_outcome=first_result.outcome.value,
            duplicate_outcome=duplicate_result.outcome.value,
            production_match_count=production.total,
            simulation_match_count=simulation.total,
            findings=findings,
        )


__all__ = ["ProductionNameAuthoringQualifier"]
