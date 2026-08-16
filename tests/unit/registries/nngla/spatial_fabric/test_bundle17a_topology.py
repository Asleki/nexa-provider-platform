from collections import Counter

from registries.nngla.spatial_fabric.topology import (
    derive_all_topology,
    derive_major_grid_topology,
    derive_reference_cell_topology,
    reciprocal_topology_findings,
)

_NEIGHBOR_FIELDS = (
    "north_id", "north_east_id", "east_id", "south_east_id",
    "south_id", "south_west_id", "west_id", "north_west_id",
)


def test_major_grid_and_reference_cell_topology_counts_are_exact_and_separate():
    assert len(derive_major_grid_topology()) == 16
    assert len(derive_reference_cell_topology()) == 1104
    assert len(derive_all_topology()) == 1120


def test_reference_cell_neighbors_are_coordinate_derived_and_reciprocal():
    cells = derive_reference_cell_topology()
    assert reciprocal_topology_findings(cells) == ()
    distribution = Counter(sum(bool(getattr(row, field)) for field in _NEIGHBOR_FIELDS) for row in cells)
    assert distribution == Counter({8: 949, 5: 51, 7: 35, 6: 30, 4: 29, 0: 3, 1: 3, 3: 3, 2: 1})


def test_offshore_reference_samples_with_no_spacing_neighbor_remain_real_missing_neighbors():
    cells = derive_reference_cell_topology()
    isolated = [row.spatial_reference_id for row in cells if not any(getattr(row, f) for f in _NEIGHBOR_FIELDS)]
    assert isolated == ["NG-SCELL-000131", "NG-SCELL-000436", "NG-SCELL-000887"]


def test_topology_never_uses_identifier_sequence_as_its_basis():
    rows = derive_all_topology()
    assert all("ID_SEQUENCE" not in row.topology_basis for row in rows)
