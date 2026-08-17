"""Bundle 17G in-memory parcel-reference reservation contract; database concurrency is deferred to 17J."""
from __future__ import annotations
from hashlib import sha256
from threading import Lock

from .contracts import CadastralSeriesDefinition, ParcelCandidateRecord, ParcelReferenceReservation


class MemoryParcelReferenceAllocator:
    def __init__(self, *, occupied_parcel_ids=(), start_sequence: int = 1) -> None:
        if start_sequence < 1:
            raise ValueError("parcel sequence must start at one or greater")
        self._occupied = set(occupied_parcel_ids)
        self._next: dict[str, int] = {}
        self._start = start_sequence
        self._reservations: dict[str, ParcelReferenceReservation] = {}
        self._lock = Lock()

    def reserve(
        self, candidate: ParcelCandidateRecord, series: CadastralSeriesDefinition,
        *, authority_runtime_mode: str = "production", source_reference: str = "bundle17g:parcel-reference-reservation",
    ) -> ParcelReferenceReservation:
        if authority_runtime_mode != "production":
            raise ValueError("Simulation may propose a parcel candidate but may not independently consume sovereign parcel numbers")
        prior = self._reservations.get(candidate.parcel_candidate_id)
        if prior is not None:
            return prior
        with self._lock:
            prior = self._reservations.get(candidate.parcel_candidate_id)
            if prior is not None:
                return prior
            key = series.parcel_prefix
            sequence = self._next.get(key, self._start)
            while True:
                parcel_id = f"{key}-{sequence:04d}"
                if parcel_id not in self._occupied:
                    break
                sequence += 1
            self._occupied.add(parcel_id)
            self._next[key] = sequence + 1
            digest = sha256(f"{candidate.parcel_candidate_id}\x1f{parcel_id}".encode()).hexdigest()
            reservation = ParcelReferenceReservation(
                reservation_id=f"parcelres:nngla:{digest}", parcel_candidate_id=candidate.parcel_candidate_id,
                parcel_id=parcel_id, cadastral_zone=series.zone_code, cadastral_series=series.series_code,
                parcel_sequence=str(sequence).zfill(4), reservation_status="RESERVED", legal_effect=False,
                canonical_parcel_registered=False, authority_runtime_mode=authority_runtime_mode, source_reference=source_reference,
            )
            self._reservations[candidate.parcel_candidate_id] = reservation
            return reservation

    def all(self) -> tuple[ParcelReferenceReservation, ...]:
        return tuple(sorted(self._reservations.values(), key=lambda row: row.parcel_id))


__all__ = ["MemoryParcelReferenceAllocator"]
