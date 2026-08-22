from registries.nngla.spatial_fabric.bundle19a.geometry import ring_is_within


def test_ring_is_within_rejects_an_edge_that_crosses_a_narrow_concavity_between_sample_points():
    # A narrow top-down notch between x=1.55 and x=1.65.  Every candidate
    # vertex is inside the polygon, but both horizontal candidate edges cross
    # the notch.  Sparse quarter-edge sampling would miss this excursion.
    sovereign_ring = (
        (0.0, 0.0),
        (4.0, 0.0),
        (4.0, 4.0),
        (1.65, 4.0),
        (1.65, 1.0),
        (1.55, 1.0),
        (1.55, 4.0),
        (0.0, 4.0),
        (0.0, 0.0),
    )
    candidate_ring = (
        (0.5, 2.0),
        (3.5, 2.0),
        (3.5, 2.5),
        (0.5, 2.5),
        (0.5, 2.0),
    )

    assert ring_is_within(candidate_ring, sovereign_ring) is False


def test_ring_is_within_accepts_a_ring_fully_inside_a_simple_polygon():
    sovereign_ring = ((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0), (0.0, 0.0))
    candidate_ring = ((1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0), (1.0, 1.0))

    assert ring_is_within(candidate_ring, sovereign_ring) is True
