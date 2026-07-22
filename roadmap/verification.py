"""
Verification and evidence analysis for the Nexa Provider Platform roadmap.

This module derives immutable verification results from milestone verification
states, tests, commit hashes, lifecycle dates, notes, and completion status.
It never mutates canonical roadmap records.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Iterable, Mapping, TypeAlias

from .models import Milestone
from .queries import MilestoneSource, all_milestones, get_by_number
from .statuses import COMPLETE_STATUSES, RoadmapStatus, StatusLike, normalize_status

VerificationState: TypeAlias = str

UNVERIFIED: Final[str] = "UNVERIFIED"
PARTIALLY_VERIFIED: Final[str] = "PARTIALLY_VERIFIED"
VERIFIED: Final[str] = "VERIFIED"
FAILED: Final[str] = "FAILED"
BLOCKED: Final[str] = "BLOCKED"
NOT_APPLICABLE: Final[str] = "NOT_APPLICABLE"

KNOWN_VERIFICATION_STATES: Final[frozenset[str]] = frozenset({
    UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED, FAILED, BLOCKED, NOT_APPLICABLE,
})
PASSING_VERIFICATION_STATES: Final[frozenset[str]] = frozenset({
    VERIFIED, NOT_APPLICABLE,
})
IN_PROGRESS_VERIFICATION_STATES: Final[frozenset[str]] = frozenset({
    PARTIALLY_VERIFIED, BLOCKED,
})
FAILING_VERIFICATION_STATES: Final[frozenset[str]] = frozenset({FAILED})
COMMIT_HASH_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-fA-F]{7,64}$")


class RoadmapVerificationError(ValueError):
    """Base exception for verification analysis errors."""


class UnknownVerificationStateError(RoadmapVerificationError):
    """Raised for an unsupported verification state."""


class MissingVerificationEvidenceError(RoadmapVerificationError):
    """Raised when one or more milestones fail verification."""


@dataclass(frozen=True, slots=True)
class VerificationPolicy:
    """Immutable rules used to verify milestones."""

    accepted_states: frozenset[str] = PASSING_VERIFICATION_STATES
    require_tests: bool = False
    minimum_passing_tests: int = 0
    require_test_information: bool = False
    require_commit_hash: bool = False
    require_started_date: bool = False
    require_completed_date: bool = False
    require_complete_status: bool = False
    complete_statuses: frozenset[RoadmapStatus] = COMPLETE_STATUSES

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "accepted_states",
            frozenset(normalize_verification_state(x) for x in self.accepted_states),
        )
        if (
            isinstance(self.minimum_passing_tests, bool)
            or not isinstance(self.minimum_passing_tests, int)
        ):
            raise TypeError("minimum_passing_tests must be an integer")
        if self.minimum_passing_tests < 0:
            raise RoadmapVerificationError(
                "minimum_passing_tests cannot be negative"
            )
        object.__setattr__(
            self,
            "complete_statuses",
            frozenset(normalize_status(x) for x in self.complete_statuses),
        )


@dataclass(frozen=True, slots=True)
class VerificationFinding:
    """One immutable verification finding."""

    code: str
    message: str
    severity: str = "ERROR"
    record_id: str | None = None
    number: str | None = None
    field: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"ERROR", "WARNING", "INFO"}:
            raise ValueError("severity must be ERROR, WARNING, or INFO")
        if not self.code.strip():
            raise ValueError("code cannot be blank")
        if not self.message.strip():
            raise ValueError("message cannot be blank")

    @property
    def is_error(self) -> bool:
        return self.severity == "ERROR"

    @property
    def is_warning(self) -> bool:
        return self.severity == "WARNING"

    @property
    def is_info(self) -> bool:
        return self.severity == "INFO"


@dataclass(frozen=True, slots=True)
class MilestoneVerification:
    """Immutable verification result for one milestone."""

    milestone: Milestone
    state: str
    passed: bool
    findings: tuple[VerificationFinding, ...]
    evidence_score: int
    evidence_items: int

    @property
    def errors(self) -> tuple[VerificationFinding, ...]:
        return tuple(x for x in self.findings if x.is_error)

    @property
    def warnings(self) -> tuple[VerificationFinding, ...]:
        return tuple(x for x in self.findings if x.is_warning)

    @property
    def is_clean(self) -> bool:
        return not self.findings

    def to_mapping(self) -> dict[str, object]:
        return {
            "record_id": self.milestone.record_id,
            "number": self.milestone.number,
            "state": self.state,
            "passed": self.passed,
            "evidence_score": self.evidence_score,
            "evidence_items": self.evidence_items,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "findings": tuple({
                "code": x.code,
                "message": x.message,
                "severity": x.severity,
                "field": x.field,
            } for x in self.findings),
        }


@dataclass(frozen=True, slots=True)
class VerificationSummary:
    """Immutable aggregate verification report."""

    total: int
    passed: int
    failed: int
    state_counts: Mapping[str, int]
    findings: tuple[VerificationFinding, ...]
    milestones_with_tests: int
    total_passing_tests: int
    milestones_with_commit_hashes: int
    milestones_with_test_information: int
    milestones_with_started_dates: int
    milestones_with_completed_dates: int

    def __post_init__(self) -> None:
        values = (
            self.total, self.passed, self.failed, self.milestones_with_tests,
            self.total_passing_tests, self.milestones_with_commit_hashes,
            self.milestones_with_test_information,
            self.milestones_with_started_dates,
            self.milestones_with_completed_dates,
        )
        if any(isinstance(x, bool) or not isinstance(x, int) for x in values):
            raise TypeError("verification summary counts must be integers")
        if any(x < 0 for x in values):
            raise RoadmapVerificationError("summary counts cannot be negative")
        if self.passed + self.failed != self.total:
            raise RoadmapVerificationError("passed plus failed must equal total")
        object.__setattr__(
            self, "state_counts", MappingProxyType(dict(self.state_counts))
        )

    @property
    def pass_rate(self) -> float:
        return 0.0 if self.total == 0 else round(self.passed / self.total * 100, 2)

    @property
    def error_count(self) -> int:
        return sum(x.is_error for x in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(x.is_warning for x in self.findings)

    @property
    def is_fully_verified(self) -> bool:
        return self.total > 0 and self.passed == self.total

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def to_mapping(self) -> dict[str, object]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.pass_rate,
            "state_counts": dict(self.state_counts),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "milestones_with_tests": self.milestones_with_tests,
            "total_passing_tests": self.total_passing_tests,
            "milestones_with_commit_hashes": self.milestones_with_commit_hashes,
            "milestones_with_test_information": self.milestones_with_test_information,
            "milestones_with_started_dates": self.milestones_with_started_dates,
            "milestones_with_completed_dates": self.milestones_with_completed_dates,
        }


def normalize_verification_state(value: object) -> str:
    """Normalize supported aliases to canonical verification states."""

    if not isinstance(value, str):
        raise TypeError("verification state must be a string")
    key = value.strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "NOT_VERIFIED": UNVERIFIED,
        "UNVERIFIED": UNVERIFIED,
        "PARTIAL": PARTIALLY_VERIFIED,
        "PARTIALLY_VERIFIED": PARTIALLY_VERIFIED,
        "VERIFIED": VERIFIED,
        "PASSED": VERIFIED,
        "PASS": VERIFIED,
        "FAILED": FAILED,
        "FAIL": FAILED,
        "BLOCKED": BLOCKED,
        "N/A": NOT_APPLICABLE,
        "NA": NOT_APPLICABLE,
        "NOT_APPLICABLE": NOT_APPLICABLE,
    }
    try:
        return aliases[key]
    except KeyError as exc:
        raise UnknownVerificationStateError(
            f"Unknown verification state {value!r}"
        ) from exc


def is_known_verification_state(value: object) -> bool:
    try:
        normalize_verification_state(value)
    except (TypeError, UnknownVerificationStateError):
        return False
    return True


def has_test_evidence(milestone: Milestone) -> bool:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    return milestone.passing_tests is not None or bool(milestone.test_information)


def has_commit_evidence(milestone: Milestone) -> bool:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    return bool(
        milestone.commit_hash
        and COMMIT_HASH_PATTERN.fullmatch(milestone.commit_hash)
    )


def evidence_items(milestone: Milestone) -> int:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    return sum((
        milestone.passing_tests is not None,
        bool(milestone.test_information),
        has_commit_evidence(milestone),
        milestone.started_date is not None,
        milestone.completed_date is not None,
        bool(milestone.notes),
    ))


def evidence_score(milestone: Milestone) -> int:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    score = 0
    score += 20 if milestone.passing_tests is not None else 0
    score += 20 if milestone.test_information else 0
    score += 20 if has_commit_evidence(milestone) else 0
    score += 10 if milestone.started_date is not None else 0
    score += 20 if milestone.completed_date is not None else 0
    score += 10 if milestone.notes else 0
    return score


def verification_findings(
    milestone: Milestone,
    *,
    policy: VerificationPolicy | None = None,
) -> tuple[VerificationFinding, ...]:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    active = policy or VerificationPolicy()
    findings: list[VerificationFinding] = []

    try:
        state = normalize_verification_state(milestone.verification_state)
    except UnknownVerificationStateError:
        return (VerificationFinding(
            code="UNKNOWN_VERIFICATION_STATE",
            message=f"Unsupported state {milestone.verification_state!r}",
            record_id=milestone.record_id,
            number=milestone.number,
            field="verification_state",
        ),)

    def add(code: str, message: str, field: str, severity: str = "ERROR") -> None:
        findings.append(VerificationFinding(
            code=code,
            message=message,
            severity=severity,
            record_id=milestone.record_id,
            number=milestone.number,
            field=field,
        ))

    if state not in active.accepted_states:
        add(
            "STATE_NOT_ACCEPTED",
            f"Verification state {state!r} is not accepted",
            "verification_state",
        )

    if active.require_tests:
        if milestone.passing_tests is None:
            add("MISSING_TEST_COUNT", "passing_tests is required", "passing_tests")
        elif milestone.passing_tests < active.minimum_passing_tests:
            add(
                "INSUFFICIENT_PASSING_TESTS",
                f"passing_tests must be at least {active.minimum_passing_tests}",
                "passing_tests",
            )

    if active.require_test_information and not milestone.test_information:
        add(
            "MISSING_TEST_INFORMATION",
            "test_information is required",
            "test_information",
        )

    if active.require_commit_hash:
        if milestone.commit_hash is None:
            add("MISSING_COMMIT_HASH", "commit_hash is required", "commit_hash")
        elif not has_commit_evidence(milestone):
            add(
                "INVALID_COMMIT_HASH",
                "commit_hash must contain 7 to 64 hexadecimal characters",
                "commit_hash",
            )

    if active.require_started_date and milestone.started_date is None:
        add("MISSING_STARTED_DATE", "started_date is required", "started_date")

    if active.require_completed_date and milestone.completed_date is None:
        add(
            "MISSING_COMPLETED_DATE",
            "completed_date is required",
            "completed_date",
        )

    if (
        active.require_complete_status
        and milestone.status not in active.complete_statuses
    ):
        add(
            "MILESTONE_STATUS_NOT_COMPLETE",
            f"Milestone status {milestone.status.value!r} is not complete",
            "status",
        )

    if milestone.passing_tests is not None and milestone.passing_tests < 0:
        add(
            "NEGATIVE_PASSING_TESTS",
            "passing_tests cannot be negative",
            "passing_tests",
        )

    if (
        milestone.passing_tests is not None
        and milestone.passing_tests > 0
        and not milestone.test_information
    ):
        add(
            "TEST_INFORMATION_RECOMMENDED",
            "test_information is recommended for positive passing_tests",
            "test_information",
            "WARNING",
        )

    return tuple(findings)


def verify_milestone(
    milestone: Milestone,
    *,
    policy: VerificationPolicy | None = None,
) -> MilestoneVerification:
    active = policy or VerificationPolicy()
    state = normalize_verification_state(milestone.verification_state)
    findings = verification_findings(milestone, policy=active)
    return MilestoneVerification(
        milestone=milestone,
        state=state,
        passed=not any(x.is_error for x in findings),
        findings=findings,
        evidence_score=evidence_score(milestone),
        evidence_items=evidence_items(milestone),
    )


def verify_collection(
    source: MilestoneSource,
    *,
    policy: VerificationPolicy | None = None,
) -> tuple[MilestoneVerification, ...]:
    active = policy or VerificationPolicy()
    return tuple(
        verify_milestone(x, policy=active) for x in all_milestones(source)
    )


def summarize_verification(
    source: MilestoneSource,
    *,
    policy: VerificationPolicy | None = None,
) -> VerificationSummary:
    records = all_milestones(source)
    results = verify_collection(records, policy=policy)
    findings = tuple(
        finding for result in results for finding in result.findings
    )
    passed = sum(result.passed for result in results)
    return VerificationSummary(
        total=len(records),
        passed=passed,
        failed=len(records) - passed,
        state_counts=Counter(result.state for result in results),
        findings=findings,
        milestones_with_tests=sum(x.passing_tests is not None for x in records),
        total_passing_tests=sum(x.passing_tests or 0 for x in records),
        milestones_with_commit_hashes=sum(has_commit_evidence(x) for x in records),
        milestones_with_test_information=sum(bool(x.test_information) for x in records),
        milestones_with_started_dates=sum(x.started_date is not None for x in records),
        milestones_with_completed_dates=sum(x.completed_date is not None for x in records),
    )


def verification_state_counts(source: MilestoneSource) -> Mapping[str, int]:
    return MappingProxyType(dict(Counter(
        normalize_verification_state(x.verification_state)
        for x in all_milestones(source)
    )))


def group_by_verification_state(
    source: MilestoneSource,
) -> Mapping[str, tuple[Milestone, ...]]:
    grouped: dict[str, list[Milestone]] = defaultdict(list)
    for item in all_milestones(source):
        grouped[normalize_verification_state(item.verification_state)].append(item)
    return MappingProxyType({
        state: tuple(values) for state, values in grouped.items()
    })


def verified_milestones(
    source: MilestoneSource,
    *,
    policy: VerificationPolicy | None = None,
) -> tuple[Milestone, ...]:
    return tuple(
        result.milestone
        for result in verify_collection(source, policy=policy)
        if result.passed
    )


def unverified_milestones(
    source: MilestoneSource,
    *,
    policy: VerificationPolicy | None = None,
) -> tuple[Milestone, ...]:
    return tuple(
        result.milestone
        for result in verify_collection(source, policy=policy)
        if not result.passed
    )


def milestones_missing_evidence(
    source: MilestoneSource,
    *,
    require_tests: bool = False,
    require_test_information: bool = False,
    require_commit_hash: bool = False,
    require_started_date: bool = False,
    require_completed_date: bool = False,
) -> tuple[Milestone, ...]:
    result: list[Milestone] = []
    for item in all_milestones(source):
        if (
            (require_tests and item.passing_tests is None)
            or (require_test_information and not item.test_information)
            or (require_commit_hash and not has_commit_evidence(item))
            or (require_started_date and item.started_date is None)
            or (require_completed_date and item.completed_date is None)
        ):
            result.append(item)
    return tuple(result)


def verification_for_milestone(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    policy: VerificationPolicy | None = None,
) -> MilestoneVerification:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    return verify_milestone(current, policy=policy)


def assert_verified(
    source: MilestoneSource,
    *,
    policy: VerificationPolicy | None = None,
) -> VerificationSummary:
    summary = summarize_verification(source, policy=policy)
    if summary.failed:
        raise MissingVerificationEvidenceError(
            f"{summary.failed} milestone(s) failed verification"
        )
    return summary


__all__ = (
    "BLOCKED", "COMMIT_HASH_PATTERN", "FAILED",
    "FAILING_VERIFICATION_STATES", "IN_PROGRESS_VERIFICATION_STATES",
    "KNOWN_VERIFICATION_STATES", "MissingVerificationEvidenceError",
    "MilestoneVerification", "NOT_APPLICABLE", "PARTIALLY_VERIFIED",
    "PASSING_VERIFICATION_STATES", "RoadmapVerificationError",
    "UNVERIFIED", "UnknownVerificationStateError", "VERIFIED",
    "VerificationFinding", "VerificationPolicy", "VerificationState",
    "VerificationSummary", "assert_verified", "evidence_items",
    "evidence_score", "group_by_verification_state",
    "has_commit_evidence", "has_test_evidence",
    "is_known_verification_state", "milestones_missing_evidence",
    "normalize_verification_state", "summarize_verification",
    "unverified_milestones", "verification_findings",
    "verification_for_milestone", "verification_state_counts",
    "verified_milestones", "verify_collection", "verify_milestone",
)
