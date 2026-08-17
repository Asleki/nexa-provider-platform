from concurrent.futures import ThreadPoolExecutor
from registries.nngla.spatial_fabric.bundle17i import MemoryTitleReferenceAllocator, load_title_series


def test_parallel_title_reference_reservations_are_unique_and_idempotent():
    allocator = MemoryTitleReferenceAllocator()
    series = load_title_series()
    with ThreadPoolExecutor(max_workers=32) as pool:
        rows = tuple(pool.map(lambda i: allocator.reserve(series, idempotency_key=f"req:{i}"), range(500)))
    assert len({r.reserved_title_id for r in rows}) == 500
    assert rows[0].reserved_title_id.startswith("NG-TTL-")
    first = allocator.reserve(series, idempotency_key="repeat")
    second = allocator.reserve(series, idempotency_key="repeat")
    assert first == second
