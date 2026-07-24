"""
Deterministic JSON storage for tracker-owned operational data.

The store is restricted to its configured tracker data directory and uses
atomic replacement. It has no method that writes architecture files.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable

from .models import TrackerRecord


class TrackerStorageError(RuntimeError):
    """Raised when tracker data cannot be read or written safely."""


@dataclass(frozen=True, slots=True)
class TrackerStore:
    data_file: Path

    def __post_init__(self) -> None:
        path = Path(self.data_file)
        if path.name in {"roadmap_data.py", "ROADMAP.md", "roadmap_frontend.py"}:
            raise TrackerStorageError("architecture-owned output paths are protected")
        object.__setattr__(self, "data_file", path)

    def load(self) -> tuple[TrackerRecord, ...]:
        if not self.data_file.exists():
            return ()
        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TrackerStorageError(
                f"unable to read tracker data: {self.data_file}"
            ) from exc

        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise TrackerStorageError("unsupported tracker storage schema")
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise TrackerStorageError("tracker records must be a JSON array")
        return tuple(TrackerRecord.from_mapping(item) for item in records)

    def save(self, records: Iterable[TrackerRecord]) -> None:
        records = tuple(records)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "records": [item.to_mapping() for item in records],
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.data_file.parent,
                prefix=f".{self.data_file.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(rendered)
                temp_name = handle.name
            os.replace(temp_name, self.data_file)
        except OSError as exc:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except Exception:
                pass
            raise TrackerStorageError(
                f"unable to write tracker data: {self.data_file}"
            ) from exc
