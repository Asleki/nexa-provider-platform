"""P006.7.2.3 immutable NNGLA spatial identifier contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import re

@dataclass(frozen=True, slots=True)
class SpatialNamespace:
    namespace_id: str
    namespace_prefix: str
    namespace_name: str
    object_family: str
    issuing_authority_code: str
    format_rule: str
    example_value: str
    immutable_after_issue: bool
    reusable_after_retirement: bool
    status: str
    effective_from: date

    def __post_init__(self) -> None:
        if not self.namespace_id.startswith("ns:"):
            raise ValueError("namespace_id must use ns: prefix")
        if self.issuing_authority_code != "NNGLA":
            raise ValueError("spatial namespace must be issued by NNGLA")
        if not self.immutable_after_issue:
            raise ValueError("NNGLA spatial identifiers must be immutable after issue")
        if self.reusable_after_retirement:
            raise ValueError("retired NNGLA spatial identifiers cannot be reused")

@dataclass(frozen=True, slots=True)
class SpatialIdentifierFormat:
    identifier_format_id: str
    namespace_id: str
    object_family: str
    prefix: str
    regex_pattern: str
    sequence_width: int | None
    case_sensitive: bool
    check_digit_rule: str
    example_identifier: str
    immutable: bool
    runtime_scoped: bool
    issuing_authority_code: str
    status: str

    def __post_init__(self) -> None:
        if not self.identifier_format_id.startswith("fmt:"):
            raise ValueError("identifier_format_id must use fmt: prefix")
        if self.issuing_authority_code != "NNGLA":
            raise ValueError("identifier format must be issued by NNGLA")
        if not self.immutable:
            raise ValueError("NNGLA spatial identifier formats must be immutable")
        if self.runtime_scoped:
            raise ValueError("NNGLA spatial identifiers are runtime-independent")
        try:
            compiled = re.compile(self.regex_pattern)
        except re.error as exc:
            raise ValueError("invalid identifier regex") from exc
        if compiled.fullmatch(self.example_identifier) is None:
            raise ValueError("example_identifier does not satisfy regex_pattern")

    def validates(self, value: str) -> bool:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.fullmatch(self.regex_pattern, value, flags=flags) is not None

class SpatialIdentifierCatalogue:
    def __init__(self, namespaces: tuple[SpatialNamespace, ...], formats: tuple[SpatialIdentifierFormat, ...]):
        ns_ids = [x.namespace_id for x in namespaces]
        fmt_ids = [x.identifier_format_id for x in formats]
        if len(ns_ids) != len(set(ns_ids)) or len(fmt_ids) != len(set(fmt_ids)):
            raise ValueError("duplicate namespace or format identifier")
        known = set(ns_ids)
        missing = {f.namespace_id for f in formats} - known
        if missing:
            raise ValueError(f"formats reference unknown namespaces: {sorted(missing)}")
        self.namespaces = tuple(namespaces)
        self.formats = tuple(formats)

    def format_for_family(self, object_family: str) -> SpatialIdentifierFormat:
        matches = [f for f in self.formats if f.object_family == object_family]
        if len(matches) != 1:
            raise KeyError(object_family)
        return matches[0]
