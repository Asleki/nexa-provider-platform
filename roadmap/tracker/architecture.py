"""
Read-only architecture bridge for the NPP Roadmap Tracker Engine.

This module converts the existing canonical RoadmapSnapshot into a small,
immutable tracker-facing snapshot. It contains no architecture write path.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Iterable, Mapping, Any


class ArchitectureBridgeError(ValueError):
    """Raised when canonical roadmap data cannot be adapted safely."""


@dataclass(frozen=True, slots=True)
class ArchitectureRecord:
    record_id: str
    number: str
    title: str
    status: str
    sequence: int
    depth: int
    parent_number: str | None

    @classmethod
    def from_object(cls, source: object) -> "ArchitectureRecord":
        def read(name: str, default: Any = None) -> Any:
            if isinstance(source, Mapping):
                return source.get(name, default)
            return getattr(source, name, default)

        status = read("status")
        if hasattr(status, "value"):
            status = status.value

        record = cls(
            record_id=str(read("record_id", "")).strip(),
            number=str(read("number", "")).strip(),
            title=str(read("title", "")).strip(),
            status=str(status or "").strip().upper(),
            sequence=int(read("sequence", 0)),
            depth=int(read("depth", 0)),
            parent_number=(
                str(read("parent_number")).strip()
                if read("parent_number") is not None
                else None
            ),
        )
        record.validate()
        return record

    def validate(self) -> None:
        if not self.record_id:
            raise ArchitectureBridgeError("architecture record_id cannot be blank")
        if not self.number.startswith("M"):
            raise ArchitectureBridgeError(
                f"invalid architecture number: {self.number!r}"
            )
        if not self.title:
            raise ArchitectureBridgeError(
                f"architecture title cannot be blank for {self.number}"
            )
        if self.sequence < 1:
            raise ArchitectureBridgeError(
                f"architecture sequence must be positive for {self.number}"
            )
        if self.depth != self.number.count("."):
            raise ArchitectureBridgeError(
                f"architecture depth mismatch for {self.number}"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "number": self.number,
            "title": self.title,
            "status": self.status,
            "sequence": self.sequence,
            "depth": self.depth,
            "parent_number": self.parent_number,
        }


@dataclass(frozen=True, slots=True)
class ArchitectureSnapshot:
    title: str
    version: str
    records: tuple[ArchitectureRecord, ...]
    sha256: str

    @classmethod
    def from_roadmap(cls, snapshot: object) -> "ArchitectureSnapshot":
        metadata = getattr(snapshot, "metadata", None)
        source_records = getattr(snapshot, "milestones", snapshot)

        try:
            records = tuple(
                sorted(
                    (ArchitectureRecord.from_object(item) for item in source_records),
                    key=lambda item: item.sequence,
                )
            )
        except TypeError as exc:
            raise ArchitectureBridgeError(
                "roadmap snapshot does not expose iterable milestones"
            ) from exc

        if not records:
            raise ArchitectureBridgeError("architecture snapshot cannot be empty")

        numbers = [record.number for record in records]
        ids = [record.record_id for record in records]
        if len(numbers) != len(set(numbers)):
            raise ArchitectureBridgeError("duplicate architecture numbers detected")
        if len(ids) != len(set(ids)):
            raise ArchitectureBridgeError("duplicate architecture record IDs detected")

        payload = [record.to_mapping() for record in records]
        digest = sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

        title = getattr(metadata, "title", "Nexa Provider Platform Roadmap")
        version = getattr(metadata, "version", "unknown")
        return cls(
            title=str(title),
            version=str(version),
            records=records,
            sha256=digest,
        )

    @property
    def by_record_id(self) -> Mapping[str, ArchitectureRecord]:
        return MappingProxyType({item.record_id: item for item in self.records})

    @property
    def by_number(self) -> Mapping[str, ArchitectureRecord]:
        return MappingProxyType({item.number: item for item in self.records})

    @property
    def completed(self) -> int:
        return sum(item.status in {"COMPLETED", "RELEASED"} for item in self.records)

    @property
    def percentage(self) -> float:
        return round((self.completed / len(self.records)) * 100, 2)

    def require_record(self, record_id: str) -> ArchitectureRecord:
        try:
            return self.by_record_id[record_id]
        except KeyError as exc:
            raise ArchitectureBridgeError(
                f"unknown architecture record ID: {record_id}"
            ) from exc
