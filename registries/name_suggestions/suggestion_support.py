"""Internal support functions shared by automatic suggestion services."""
from __future__ import annotations
from registries.names import CanonicalName, NameKind, NameRepository, NameSearchQuery
from .first_eligible_selection_policy import FirstEligibleSelectionPolicy
from .suggestion_errors import NameSuggestionCandidateNotFoundError
from .suggestion_selection_policy import SuggestionSelectionPolicy


def normalize_runtime_mode(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("runtime_mode must be text.")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("runtime_mode cannot be empty.")
    return normalized


def require_repository(value: object) -> NameRepository:
    if not isinstance(value, NameRepository):
        raise TypeError("repository must implement NameRepository.")
    return value


def require_policy(value: object | None) -> SuggestionSelectionPolicy:
    if value is None:
        return FirstEligibleSelectionPolicy()
    if not isinstance(value, SuggestionSelectionPolicy):
        raise TypeError("selection_policy must implement SuggestionSelectionPolicy.")
    return value


def select_candidate(
    repository: NameRepository,
    selection_policy: SuggestionSelectionPolicy,
    name_kind: NameKind,
    runtime_mode: str,
) -> CanonicalName:
    result = repository.search(
        NameSearchQuery(
            text="",
            name_kind=name_kind,
            runtime_mode=runtime_mode,
            limit=1000,
        )
    )
    try:
        candidate = selection_policy.select(result.records)
    except NameSuggestionCandidateNotFoundError as exc:
        raise NameSuggestionCandidateNotFoundError(
            f"no active {name_kind.value} candidate exists in runtime_mode "
            f"{runtime_mode!r}."
        ) from exc
    if candidate.name_kind is not name_kind:
        raise ValueError("selection policy returned a candidate of the wrong name kind.")
    if candidate.metadata.runtime_mode != runtime_mode:
        raise ValueError("selection policy returned a candidate from the wrong runtime_mode.")
    return candidate


def validate_component(value: object, kind: NameKind, field_name: str) -> CanonicalName:
    if not isinstance(value, CanonicalName):
        raise TypeError(f"{field_name} must be CanonicalName.")
    if value.name_kind is not kind:
        raise ValueError(f"{field_name} must have kind {kind.value}.")
    return value
