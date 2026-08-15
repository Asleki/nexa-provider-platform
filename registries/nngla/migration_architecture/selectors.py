"""P006.7.11.4 deterministic NNGLA plan selectors."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Iterable, Mapping

from .limits import validate_batch_limit
from .source_catalogue import SourceRecord


class SelectorKind(str, Enum):
    ALL = "ALL"
    FIELD_EQUALS = "FIELD_EQUALS"
    FIELD_IN = "FIELD_IN"
    EXACT_IDS = "EXACT_IDS"


@dataclass(frozen=True, slots=True)
class Selector:
    kind: SelectorKind = SelectorKind.ALL
    field: str | None = None
    values: tuple[str, ...] = ()
    exact_ids: tuple[str, ...] = ()
    after_id: str | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        failures = validate_batch_limit(self.limit)
        if failures:
            raise ValueError(failures[0])
        if self.kind in {SelectorKind.FIELD_EQUALS, SelectorKind.FIELD_IN} and not self.field:
            raise ValueError("field selector requires field")
        if self.kind is SelectorKind.FIELD_EQUALS and len(self.values) != 1:
            raise ValueError("FIELD_EQUALS requires exactly one value")
        if self.kind is SelectorKind.FIELD_IN and not self.values:
            raise ValueError("FIELD_IN requires values")
        if self.kind is SelectorKind.EXACT_IDS and not self.exact_ids:
            raise ValueError("EXACT_IDS requires exact_ids")


def select_records(records: Iterable[SourceRecord], selector: Selector) -> tuple[SourceRecord, ...]:
    ordered = sorted(records, key=lambda record: record.source_id)
    if selector.kind is SelectorKind.FIELD_EQUALS:
        value = selector.values[0]
        ordered = [record for record in ordered if str(record.payload.get(selector.field or "", "")) == value]
    elif selector.kind is SelectorKind.FIELD_IN:
        allowed = set(selector.values)
        ordered = [record for record in ordered if str(record.payload.get(selector.field or "", "")) in allowed]
    elif selector.kind is SelectorKind.EXACT_IDS:
        requested = set(selector.exact_ids)
        ordered = [record for record in ordered if record.source_id in requested]
        missing = sorted(requested - {record.source_id for record in ordered})
        if missing:
            raise ValueError(f"requested source IDs are missing: {missing[:5]}")
    if selector.after_id is not None:
        ordered = [record for record in ordered if record.source_id > selector.after_id]
    if selector.limit is not None:
        ordered = ordered[: selector.limit]
    return tuple(ordered)


__all__ = ["SelectorKind", "Selector", "select_records"]
