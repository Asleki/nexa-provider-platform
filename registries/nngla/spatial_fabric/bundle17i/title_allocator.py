"""Bundle 17I thread-safe title-reference allocator; database stress/recovery is attacked again in Bundle 17J."""
from __future__ import annotations

from hashlib import sha256
from threading import Lock
import re

from .contracts import TitleNumberSeriesDefinition, TitleReferenceReservation


class MemoryTitleReferenceAllocator:
    def __init__(self, *, occupied_title_ids=(), start_sequence: int = 1) -> None:
        if start_sequence < 1:
            raise ValueError("title sequence must start at one or greater")
        self._occupied = set(occupied_title_ids)
        self._next = start_sequence
        self._by_idempotency: dict[str, TitleReferenceReservation] = {}
        self._lock = Lock()

    def reserve(
        self, series: TitleNumberSeriesDefinition, *, idempotency_key: str,
        parcel_id: str = "", holder_reference: str = "", authority_runtime_mode: str = "production",
        source_reference: str = "bundle17i:title-reference-reservation",
    ) -> TitleReferenceReservation:
        if authority_runtime_mode != "production":
            raise ValueError("Simulation may propose legal activity but may not independently consume sovereign title references")
        prior = self._by_idempotency.get(idempotency_key)
        if prior is not None:
            return prior
        with self._lock:
            prior = self._by_idempotency.get(idempotency_key)
            if prior is not None:
                return prior
            sequence = max(self._next, series.minimum_sequence)
            while True:
                title_id = f"{series.prefix}{sequence:0{series.sequence_width}d}"
                if title_id not in self._occupied:
                    break
                sequence += 1
            self._occupied.add(title_id)
            self._next = sequence + 1
            digest = sha256(f"{series.series_id}\x1f{title_id}\x1f{idempotency_key}".encode()).hexdigest()
            reservation = TitleReferenceReservation(
                reservation_id=f"titleres:nngla:{digest}", series_id=series.series_id,
                reserved_title_id=title_id, parcel_id=parcel_id, holder_reference=holder_reference,
                idempotency_key=idempotency_key, reservation_status="TITLE_NUMBER_RESERVED",
                legal_title_exists=False, authority_runtime_mode=authority_runtime_mode, source_reference=source_reference,
            )
            self._by_idempotency[idempotency_key] = reservation
            return reservation

    def all(self) -> tuple[TitleReferenceReservation, ...]:
        return tuple(sorted(self._by_idempotency.values(), key=lambda row: row.reserved_title_id))


__all__ = ["MemoryTitleReferenceAllocator"]
