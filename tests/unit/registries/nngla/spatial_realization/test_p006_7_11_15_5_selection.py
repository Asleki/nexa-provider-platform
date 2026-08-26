import pytest
from registries.nngla.spatial_realization.selection import eligible_city_root_ids,normalize_city_root_ids,selection_digest


def test_arbitrary_supported_city_batch_sizes_use_one_normalizer():
    roots=eligible_city_root_ids()
    for size in (1,2,3,5,6,7,8):
        selected=roots[:size]
        assert normalize_city_root_ids(reversed(selected))==selected


def test_selection_order_does_not_change_digest():
    roots=eligible_city_root_ids()[:3]
    assert selection_digest(roots)==selection_digest(reversed(roots))


def test_duplicate_unknown_and_noncanonical_roots_fail_closed():
    roots=eligible_city_root_ids()
    with pytest.raises(ValueError,match='DUPLICATE_EXECUTION_ROOT'):normalize_city_root_ids([roots[0],roots[0]])
    with pytest.raises(ValueError,match='UNKNOWN_OR_NON_CITY_EXECUTION_ROOT'):normalize_city_root_ids(['NG-PLC-000002'])
    with pytest.raises(ValueError):normalize_city_root_ids(['Orivane'])
