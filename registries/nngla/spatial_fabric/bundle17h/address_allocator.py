"""Bundle 17H deterministic concurrent address-number reservation engine."""
from __future__ import annotations

from hashlib import sha256
from threading import Lock
import re

from .contracts import AddressNumberReservation, AddressSeriesDefinition


def normalize_address_number(value: str) -> str:
    text = re.sub(r"\s+", "", str(value).strip().upper())
    if not text:
        raise ValueError("address number cannot be blank")
    if not re.fullmatch(r"[0-9A-Z][0-9A-Z/-]{0,15}", text):
        raise ValueError("address number is outside governed bounded human-readable format")
    return text


class AddressNumberCollisionError(ValueError):
    pass


class MemoryAddressAllocator:
    """Thread-safe proof allocator. PostgreSQL row locking is specified by the Bundle 17H SQL contract."""

    def __init__(self, *, occupied_address_ids=(), start_address_sequence: int = 1) -> None:
        if start_address_sequence < 1:
            raise ValueError("address identity sequence must start at one or greater")
        self._lock = Lock()
        self._series_next: dict[str, int] = {}
        self._occupied_numbers: set[tuple[str, str]] = set()
        self._occupied_address_ids = set(occupied_address_ids)
        self._next_address_sequence = start_address_sequence
        self._by_idempotency: dict[tuple[str, str], AddressNumberReservation] = {}
        self._reservations: list[AddressNumberReservation] = []

    def _allocate_address_id(self) -> str:
        while True:
            address_id = f"NG-ADR-{self._next_address_sequence:06d}"
            self._next_address_sequence += 1
            if address_id not in self._occupied_address_ids:
                self._occupied_address_ids.add(address_id)
                return address_id

    def reserve_next(
        self, series: AddressSeriesDefinition, *, site_id: str, idempotency_key: str,
        authority_runtime_mode: str = "production", source_reference: str = "bundle17h:address-reservation",
    ) -> AddressNumberReservation:
        if authority_runtime_mode != "production":
            raise ValueError("Simulation may propose addressable sites but may not independently consume sovereign address IDs/numbers")
        key = (series.series_id, idempotency_key)
        prior = self._by_idempotency.get(key)
        if prior is not None:
            return prior
        with self._lock:
            prior = self._by_idempotency.get(key)
            if prior is not None:
                return prior
            number = self._series_next.get(series.series_id, series.start_number)
            while (series.series_id, normalize_address_number(str(number))) in self._occupied_numbers:
                number += series.sequence_step
            self._series_next[series.series_id] = number + series.sequence_step
            return self._reserve_locked(
                series, site_id=site_id, display_number=str(number), idempotency_key=idempotency_key,
                authority_runtime_mode=authority_runtime_mode, source_reference=source_reference,
            )

    def reserve_specific(
        self, series: AddressSeriesDefinition, *, site_id: str, display_number: str, idempotency_key: str,
        authority_runtime_mode: str = "production", source_reference: str = "bundle17h:address-reservation",
    ) -> AddressNumberReservation:
        if authority_runtime_mode != "production":
            raise ValueError("sovereign address reservation requires production authority")
        key = (series.series_id, idempotency_key)
        prior = self._by_idempotency.get(key)
        if prior is not None:
            return prior
        with self._lock:
            prior = self._by_idempotency.get(key)
            if prior is not None:
                return prior
            return self._reserve_locked(
                series, site_id=site_id, display_number=display_number, idempotency_key=idempotency_key,
                authority_runtime_mode=authority_runtime_mode, source_reference=source_reference,
            )

    def _reserve_locked(
        self, series: AddressSeriesDefinition, *, site_id: str, display_number: str, idempotency_key: str,
        authority_runtime_mode: str, source_reference: str,
    ) -> AddressNumberReservation:
        normalized = normalize_address_number(display_number)
        number_key = (series.series_id, normalized)
        if number_key in self._occupied_numbers:
            raise AddressNumberCollisionError(f"same-scope address number already reserved: {series.series_id}/{normalized}")
        address_id = self._allocate_address_id()
        digest = sha256(f"{series.series_id}\x1f{site_id}\x1f{normalized}\x1f{idempotency_key}\x1f{address_id}".encode()).hexdigest()
        reservation = AddressNumberReservation(
            reservation_id=f"addrres:nngla:{digest}", series_id=series.series_id, site_id=site_id,
            reserved_address_id=address_id, display_address_number=str(display_number), normalized_number_key=normalized,
            idempotency_key=idempotency_key, reservation_status="RESERVED", canonical_address_created=False,
            authority_runtime_mode=authority_runtime_mode, source_reference=source_reference,
        )
        self._occupied_numbers.add(number_key)
        self._by_idempotency[(series.series_id, idempotency_key)] = reservation
        self._reservations.append(reservation)
        return reservation

    def all(self) -> tuple[AddressNumberReservation, ...]:
        return tuple(self._reservations)


__all__ = ["normalize_address_number", "AddressNumberCollisionError", "MemoryAddressAllocator"]
