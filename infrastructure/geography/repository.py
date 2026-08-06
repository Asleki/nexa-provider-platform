"""Repository ports and safe in-memory adapter for governed world geometry."""
from __future__ import annotations

from typing import Protocol

from .contracts import WorldBoundaryPublication


class WorldBoundaryRepository(Protocol):
    def save(self, publication: WorldBoundaryPublication) -> None: ...
    def get_active(self) -> WorldBoundaryPublication | None: ...


class InMemoryWorldBoundaryRepository:
    def __init__(self, publications=()) -> None:
        self._publications = {item.publication_id: item for item in publications}

    def save(self, publication: WorldBoundaryPublication) -> None:
        self._publications[publication.publication_id] = publication

    def get_active(self) -> WorldBoundaryPublication | None:
        if not self._publications:
            return None
        return sorted(
            self._publications.values(),
            key=lambda item: (item.identity.version, item.publication_id),
        )[-1]
