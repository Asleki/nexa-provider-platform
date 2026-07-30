"""Policy-driven duplicate controls for M009.2.7."""
from __future__ import annotations
from registries.names import CanonicalName
from .suggestion_duplicate_evaluation import SuggestionDuplicateEvaluation
from .suggestion_duplicate_policy import SuggestionDuplicatePolicy
from .suggestion_selection_policy import SuggestionSelectionPolicy


def _text_set(name: str, values: object) -> frozenset[str]:
    if values is None:
        return frozenset()
    if isinstance(values, str) or not isinstance(values, (tuple, list, set, frozenset)):
        raise TypeError(f"{name} must be an iterable of text values.")
    result: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must contain non-empty text values.")
        result.add(value.strip())
    return frozenset(result)


class SuggestionDuplicateControl:
    def __init__(self, policy: SuggestionDuplicatePolicy | None = None) -> None:
        if policy is None:
            policy = SuggestionDuplicatePolicy.strict()
        if not isinstance(policy, SuggestionDuplicatePolicy):
            raise TypeError("policy must be SuggestionDuplicatePolicy.")
        self._policy = policy

    @property
    def policy(self) -> SuggestionDuplicatePolicy:
        return self._policy

    def evaluate(
        self,
        candidate: CanonicalName,
        *,
        excluded_name_ids: object = (),
        excluded_values: object = (),
        selected: tuple[CanonicalName, ...] = (),
    ) -> SuggestionDuplicateEvaluation:
        if not isinstance(candidate, CanonicalName):
            raise TypeError("candidate must be CanonicalName.")
        ids = _text_set("excluded_name_ids", excluded_name_ids)
        values = _text_set("excluded_values", excluded_values)
        selected = tuple(selected)
        if any(not isinstance(record, CanonicalName) for record in selected):
            raise TypeError("selected must contain only CanonicalName records.")
        reasons: list[str] = []
        if self._policy.compare_canonical_name_ids:
            if candidate.name_id in ids:
                reasons.append("excluded_name_id")
            if self._policy.reject_within_result and any(
                record.name_id == candidate.name_id for record in selected
            ):
                reasons.append("selected_name_id")
        if self._policy.compare_normalized_values:
            if candidate.search_value in values:
                reasons.append("excluded_normalized_value")
            if self._policy.reject_within_result and any(
                record.search_value == candidate.search_value for record in selected
            ):
                reasons.append("selected_normalized_value")
        return SuggestionDuplicateEvaluation(
            candidate.name_id,
            candidate.search_value,
            bool(reasons),
            tuple(reasons),
        )

    def eligible_candidates(
        self,
        candidates: tuple[CanonicalName, ...],
        *,
        excluded_name_ids: object = (),
        excluded_values: object = (),
        selected: tuple[CanonicalName, ...] = (),
    ) -> tuple[CanonicalName, ...]:
        if not isinstance(candidates, tuple):
            raise TypeError("candidates must be a tuple of CanonicalName records.")
        if any(not isinstance(candidate, CanonicalName) for candidate in candidates):
            raise TypeError("candidates must contain only CanonicalName records.")
        return tuple(
            candidate
            for candidate in candidates
            if not self.evaluate(
                candidate,
                excluded_name_ids=excluded_name_ids,
                excluded_values=excluded_values,
                selected=selected,
            ).duplicate
        )


class DuplicateAwareSelectionPolicy(SuggestionSelectionPolicy):
    """Per-request adapter that applies duplicate controls before base selection."""

    def __init__(
        self,
        base_policy: SuggestionSelectionPolicy,
        duplicate_control: SuggestionDuplicateControl,
        *,
        excluded_name_ids: object = (),
        excluded_values: object = (),
    ) -> None:
        if not isinstance(base_policy, SuggestionSelectionPolicy):
            raise TypeError("base_policy must implement SuggestionSelectionPolicy.")
        if not isinstance(duplicate_control, SuggestionDuplicateControl):
            raise TypeError("duplicate_control must be SuggestionDuplicateControl.")
        self._base_policy = base_policy
        self._duplicate_control = duplicate_control
        self._excluded_name_ids = _text_set("excluded_name_ids", excluded_name_ids)
        self._excluded_values = _text_set("excluded_values", excluded_values)
        self._selected: list[CanonicalName] = []

    @property
    def selected(self) -> tuple[CanonicalName, ...]:
        return tuple(self._selected)

    def select(self, candidates: tuple[CanonicalName, ...]) -> CanonicalName:
        eligible = self._duplicate_control.eligible_candidates(
            candidates,
            excluded_name_ids=self._excluded_name_ids,
            excluded_values=self._excluded_values,
            selected=tuple(self._selected),
        )
        selected = self._base_policy.select(eligible)
        self._selected.append(selected)
        return selected


__all__ = ["DuplicateAwareSelectionPolicy", "SuggestionDuplicateControl"]
