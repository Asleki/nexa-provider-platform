"""Framework-neutral facade completing the M009.2 Name Suggestion Engine."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Mapping
from registries.names import CanonicalName, NameKind, NameRepository
from .first_eligible_selection_policy import FirstEligibleSelectionPolicy
from .full_name_composition import FullNameComposition
from .full_name_suggestion import FullNameSuggestion
from .full_name_suggestion_service import FullNameSuggestionService
from .pair_name_suggestion import PairNameSuggestion
from .pair_name_suggestion_service import PairNameSuggestionService
from .single_name_suggestion import SingleNameSuggestion
from .single_name_suggestion_service import SingleNameSuggestionService
from .suggestion_api_contract import SuggestionApiContract
from .suggestion_api_errors import SuggestionApiValidationError
from .suggestion_api_operation import SuggestionApiOperation
from .suggestion_api_request import SuggestionApiRequest
from .suggestion_api_response import SuggestionApiResponse
from .suggestion_duplicate_control import DuplicateAwareSelectionPolicy, SuggestionDuplicateControl
from .suggestion_duplicate_policy import SuggestionDuplicatePolicy
from .suggestion_name_normalizer import SuggestionNameNormalizer
from .suggestion_selection_policy import SuggestionSelectionPolicy
from .suggestion_support import require_policy, require_repository
from .trio_name_suggestion import TrioNameSuggestion
from .trio_name_suggestion_service import TrioNameSuggestionService


def _iterable_text(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key, ())
    if isinstance(value, str) or not isinstance(value, (tuple, list, set, frozenset)):
        raise SuggestionApiValidationError(f"{key} must be an iterable of text values.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise SuggestionApiValidationError(f"{key} must contain non-empty text values.")
        normalized = item.strip()
        if normalized not in result:
            result.append(normalized)
    return tuple(result)


def _result_data(result: object) -> dict[str, object]:
    components = getattr(result, "components")
    return {
        "component_ids": list(getattr(result, "component_ids")),
        "component_count": getattr(result, "component_count"),
        "rendered_value": getattr(result, "rendered_value"),
        "runtime_mode": getattr(result, "runtime_mode"),
        "components": [
            {
                "canonical_name_id": record.name_id,
                "canonical_value": record.canonical_value,
                "comparison_value": record.search_value,
                "name_kind": record.name_kind.value,
            }
            for record in components
        ],
    }


class SuggestionApi(SuggestionApiContract):
    def __init__(
        self,
        repository: NameRepository,
        selection_policy: SuggestionSelectionPolicy | None = None,
        normalizer: SuggestionNameNormalizer | None = None,
        duplicate_policy: SuggestionDuplicatePolicy | None = None,
        clock=None,
    ) -> None:
        self._repository = require_repository(repository)
        self._selection_policy = require_policy(selection_policy)
        if normalizer is None:
            normalizer = SuggestionNameNormalizer()
        if not isinstance(normalizer, SuggestionNameNormalizer):
            raise TypeError("normalizer must be SuggestionNameNormalizer.")
        if duplicate_policy is None:
            duplicate_policy = SuggestionDuplicatePolicy.strict()
        if not isinstance(duplicate_policy, SuggestionDuplicatePolicy):
            raise TypeError("duplicate_policy must be SuggestionDuplicatePolicy.")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable or None.")
        self._normalizer = normalizer
        self._duplicate_policy = duplicate_policy
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _completed_at(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise TypeError("clock must return a timezone-aware datetime.")
        return value

    def _policy_for(self, payload: Mapping[str, Any]) -> DuplicateAwareSelectionPolicy:
        excluded_values = tuple(
            self._normalizer.normalize(value).comparison_value
            for value in _iterable_text(payload, "excluded_values")
        )
        return DuplicateAwareSelectionPolicy(
            self._selection_policy,
            SuggestionDuplicateControl(self._duplicate_policy),
            excluded_name_ids=_iterable_text(payload, "excluded_name_ids"),
            excluded_values=excluded_values,
        )

    def _execute_operation(self, request: SuggestionApiRequest) -> dict[str, object]:
        payload = request.payload
        operation = request.operation
        if operation is SuggestionApiOperation.NORMALIZE:
            if "value" not in payload:
                raise SuggestionApiValidationError("payload.value is required.")
            return self._normalizer.normalize(payload["value"]).to_dict()
        if operation is SuggestionApiOperation.CHECK_DUPLICATE:
            candidate_id = payload.get("canonical_name_id")
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise SuggestionApiValidationError("payload.canonical_name_id is required.")
            candidate = self._repository.get(candidate_id.strip())
            if candidate.metadata.runtime_mode != request.runtime_mode:
                raise SuggestionApiValidationError("candidate runtime_mode does not match request runtime_mode.")
            excluded_values = tuple(
                self._normalizer.normalize(value).comparison_value
                for value in _iterable_text(payload, "excluded_values")
            )
            evaluation = SuggestionDuplicateControl(self._duplicate_policy).evaluate(
                candidate,
                excluded_name_ids=_iterable_text(payload, "excluded_name_ids"),
                excluded_values=excluded_values,
            )
            return evaluation.to_dict()
        policy = self._policy_for(payload)
        if operation is SuggestionApiOperation.SUGGEST_SINGLE:
            if "name_kind" not in payload:
                raise SuggestionApiValidationError("payload.name_kind is required.")
            result = SingleNameSuggestionService(self._repository, policy).suggest(
                SingleNameSuggestion(NameKind.parse(payload["name_kind"]), request.runtime_mode)
            )
        elif operation is SuggestionApiOperation.SUGGEST_PAIR:
            result = PairNameSuggestionService(self._repository, policy).suggest(
                PairNameSuggestion(request.runtime_mode)
            )
        elif operation is SuggestionApiOperation.SUGGEST_TRIO:
            result = TrioNameSuggestionService(self._repository, policy).suggest(
                TrioNameSuggestion(request.runtime_mode)
            )
        elif operation is SuggestionApiOperation.SUGGEST_FULL_NAME:
            result = FullNameSuggestionService(self._repository, policy).suggest(
                FullNameSuggestion(
                    payload.get("composition", FullNameComposition.FIRST_MIDDLE_SURNAME),
                    request.runtime_mode,
                )
            )
        else:
            raise SuggestionApiValidationError(f"unsupported operation: {operation.value}.")
        data = _result_data(result)
        data["duplicate_policy"] = self._duplicate_policy.to_dict()
        if hasattr(result, "composition"):
            data["composition"] = result.composition.value
        return data

    def execute(self, request: SuggestionApiRequest) -> SuggestionApiResponse:
        if not isinstance(request, SuggestionApiRequest):
            raise TypeError("request must be SuggestionApiRequest.")
        try:
            data = self._execute_operation(request)
            return SuggestionApiResponse.succeeded(
                request_id=request.request_id,
                operation=request.operation,
                completed_at=self._completed_at(),
                data=data,
                metadata=request.metadata,
            )
        except Exception as exc:
            return SuggestionApiResponse.failed(
                request_id=request.request_id,
                operation=request.operation,
                completed_at=self._completed_at(),
                error={
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "category": "validation" if isinstance(exc, (TypeError, ValueError, SuggestionApiValidationError)) else "operation",
                },
                metadata=request.metadata,
            )


__all__ = ["SuggestionApi"]
