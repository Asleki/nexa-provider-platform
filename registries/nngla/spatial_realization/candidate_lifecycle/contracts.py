"""Immutable contracts for P006.7.11.15.5 Delivery-2 governed candidates."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping

_SHA = re.compile(r"^[0-9a-f]{64}$")


class CandidateRuntime(str, Enum):
    SIMULATION = "simulation"
    PRODUCTION = "production"


class CandidateLifecycleStatus(str, Enum):
    GOVERNANCE_REQUIRED = "GOVERNANCE_REQUIRED"
    READY_FOR_CANDIDATE_QUALIFICATION = "READY_FOR_CANDIDATE_QUALIFICATION"
    CANDIDATE_QUALIFIED = "CANDIDATE_QUALIFIED"
    CANDIDATE_REJECTED = "CANDIDATE_REJECTED"
    CANDIDATE_STALE = "CANDIDATE_STALE"
    CANDIDATE_SUPERSEDED = "CANDIDATE_SUPERSEDED"


@dataclass(frozen=True, slots=True)
class GovernedDecisionRecord:
    decision_id: str
    fabric_run_id: str
    scope_fingerprint: str
    decision_type: str
    target_id: str
    target_geometry_sha256: str
    owner_subject_id: str
    decision_kind: str
    decision_reference: str
    rationale: str
    reviewer_actor_id: str
    approver_actor_id: str
    runtime_mode: CandidateRuntime

    def __post_init__(self) -> None:
        if not self.decision_id.startswith("fabric-decision:nngla:"):
            raise ValueError("governed decision identity namespace required")
        if not self.fabric_run_id.startswith("fabric-run:nngla:"):
            raise ValueError("governed decision must bind an exact fabric run")
        if _SHA.fullmatch(self.scope_fingerprint) is None:
            raise ValueError("governed decision scope fingerprint must be SHA-256")
        if self.decision_type not in {"FACE_ASSIGNMENT", "BOUNDARY_CONFLICT"}:
            raise ValueError("unsupported governed decision type")
        if _SHA.fullmatch(self.target_geometry_sha256) is None:
            raise ValueError("decision target geometry hash must be SHA-256")
        if not self.target_id.startswith(("fabric-face:nngla:", "fabric-defect:nngla:")):
            raise ValueError("decision target identity namespace required")
        if not self.reviewer_actor_id or not self.approver_actor_id or self.reviewer_actor_id == self.approver_actor_id:
            raise ValueError("distinct reviewer and approver are required")
        if not self.decision_reference.strip() or not self.rationale.strip():
            raise ValueError("decision evidence is required")


@dataclass(frozen=True, slots=True)
class CandidatePackage:
    fabric_run_id: str
    requested_root_place_id: str
    parent_administrative_area_id: str
    fabric_level: str
    runtime_mode: CandidateRuntime
    scope_fingerprint: str
    input_digest: str
    runtime_signature_digest: str
    edge_graph_sha256: str
    face_set_sha256: str
    assignment_sha256: str
    qualification_sha256: str
    author_actor_id: str
    lifecycle_status: CandidateLifecycleStatus
    parent_candidate_id: str = ""
    parent_candidate_geometry_sha256: str = ""
    inputs: tuple[Mapping[str, object], ...] = ()
    edges: tuple[Mapping[str, object], ...] = ()
    faces: tuple[Mapping[str, object], ...] = ()
    defects: tuple[Mapping[str, object], ...] = ()
    decisions: tuple[GovernedDecisionRecord, ...] = ()
    assignments: tuple[Mapping[str, object], ...] = ()
    sibling_candidates: tuple[Mapping[str, object], ...] = ()
    package_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.fabric_run_id.startswith("fabric-run:nngla:"):
            raise ValueError("fabric run identity namespace required")
        for value, label in (
            (self.scope_fingerprint, "scope fingerprint"),
            (self.input_digest, "input digest"),
            (self.runtime_signature_digest, "runtime signature digest"),
            (self.edge_graph_sha256, "edge graph digest"),
            (self.face_set_sha256, "face set digest"),
        ):
            if _SHA.fullmatch(value) is None:
                raise ValueError(f"{label} must be SHA-256")
        for value, label in (
            (self.assignment_sha256, "assignment digest"),
            (self.qualification_sha256, "qualification digest"),
            (self.parent_candidate_geometry_sha256, "parent candidate geometry digest"),
            (self.package_sha256, "package digest"),
        ):
            if value and _SHA.fullmatch(value) is None:
                raise ValueError(f"{label} must be SHA-256 when present")
        if bool(self.parent_candidate_id) != bool(self.parent_candidate_geometry_sha256):
            raise ValueError("recursive candidate requires both parent candidate id and geometry hash")
        if not self.author_actor_id.strip():
            raise ValueError("candidate package author is required")


@dataclass(frozen=True, slots=True)
class CandidateQualificationDecision:
    qualification_id: str
    fabric_run_id: str
    package_sha256: str
    qualifier_actor_id: str
    status: CandidateLifecycleStatus
    valid_all: bool
    every_child_covered_by_parent: bool
    union_covered_by_parent: bool
    parent_covered_by_union: bool
    symmetric_difference_m2: float
    positive_overlap_m2: float
    decision_sha256: str

    def __post_init__(self) -> None:
        if not self.qualification_id.startswith("fabric-qualification:nngla:"):
            raise ValueError("candidate qualification identity namespace required")
        if self.status not in {CandidateLifecycleStatus.CANDIDATE_QUALIFIED, CandidateLifecycleStatus.CANDIDATE_REJECTED}:
            raise ValueError("qualification decision status must be qualified or rejected")
        if _SHA.fullmatch(self.package_sha256) is None or _SHA.fullmatch(self.decision_sha256) is None:
            raise ValueError("qualification package/decision hashes must be SHA-256")
        if not self.qualifier_actor_id.strip():
            raise ValueError("qualifier actor is required")


__all__ = [
    "CandidateRuntime", "CandidateLifecycleStatus", "GovernedDecisionRecord",
    "CandidatePackage", "CandidateQualificationDecision",
]
