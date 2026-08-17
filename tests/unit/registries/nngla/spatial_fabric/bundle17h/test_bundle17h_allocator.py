from concurrent.futures import ThreadPoolExecutor
import pytest
from registries.nngla.spatial_fabric.bundle17h import (
    AddressNumberCollisionError, AddressSeriesDefinition, MemoryAddressAllocator,
)


def _series(name="a", road="NG-RD-000001", start=1):
    return AddressSeriesDefinition(f"addrseries:nngla:{name}", road, "", "SEQUENTIAL", "ROAD", road, start, 1, "INTEGER", "NONE", False)


def test_1000_parallel_address_allocations_have_unique_ids_and_same_scope_numbers():
    allocator = MemoryAddressAllocator()
    series = _series()
    def reserve(i):
        return allocator.reserve_next(series, site_id=f"site:nngla:{i}", idempotency_key=f"req:{i}")
    with ThreadPoolExecutor(max_workers=48) as pool:
        rows = tuple(pool.map(reserve, range(1000)))
    assert len(rows) == 1000
    assert len({r.reserved_address_id for r in rows}) == 1000
    assert len({r.normalized_number_key for r in rows}) == 1000
    assert {int(r.display_address_number) for r in rows} == set(range(1,1001))


def test_same_scope_duplicate_fails_but_different_scope_same_visible_number_is_valid():
    allocator = MemoryAddressAllocator()
    a = _series("a", "NG-RD-000001")
    b = _series("b", "NG-RD-000002")
    allocator.reserve_specific(a, site_id="site:nngla:a", display_number="14", idempotency_key="a")
    with pytest.raises(AddressNumberCollisionError):
        allocator.reserve_specific(a, site_id="site:nngla:b", display_number="14", idempotency_key="b")
    other = allocator.reserve_specific(b, site_id="site:nngla:c", display_number="14", idempotency_key="c")
    assert other.display_address_number == "14"


def test_address_reservation_is_idempotent_per_series_request():
    allocator = MemoryAddressAllocator()
    series = _series()
    first = allocator.reserve_next(series, site_id="site:nngla:a", idempotency_key="same")
    second = allocator.reserve_next(series, site_id="site:nngla:a", idempotency_key="same")
    assert first == second
    assert len(allocator.all()) == 1
