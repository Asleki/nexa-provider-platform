"""
============================================================
Nexa Provider Platform
File: shared/repositories/base_repository.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Base implementation shared by concrete repository classes.
Provides immutable repository metadata and common validation.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from .repository_interface import RepositoryInterface
from .repository_types import RepositoryType


class BaseRepository(RepositoryInterface, ABC):
    """Common functionality for repository implementations."""

    def __init__(
        self,
        repository_name: str,
        id_field: str,
        repository_type: RepositoryType = RepositoryType.LOCAL,
    ) -> None:
        if not repository_name or not repository_name.strip():
            raise ValueError("repository_name must not be empty.")
        if not id_field or not id_field.strip():
            raise ValueError("id_field must not be empty.")

        self._repository_name = repository_name.strip()
        self._id_field = id_field.strip()
        self._repository_type = repository_type

    @property
    def repository_name(self) -> str:
        return self._repository_name

    @property
    def repository_type(self) -> str:
        return self._repository_type.value

    @property
    def id_field(self) -> str:
        return self._id_field

    def validate_identifier(self, record_id: Any) -> str:
        """Validate and normalize repository identifiers."""
        if record_id is None:
            raise ValueError("record_id must not be None.")

        if not isinstance(record_id, str):
            raise TypeError("record_id must be a string.")

        value = record_id.strip()

        if not value:
            raise ValueError("record_id must not be empty.")

        return value


__all__ = ["BaseRepository"]
