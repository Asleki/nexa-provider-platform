import pytest

from registries.country.contracts import SovereignBoundaryAssociation


def test_p006_7_1_6_boundary_association_references_locked_geography_without_copying_geometry():
    association = SovereignBoundaryAssociation(
        association_id="country-boundary:novegeo:v002",
        country_id="country:novegeo",
        boundary_id="boundary:novegeo:sovereign",
        boundary_version=2,
        coordinate_reference_id="crs:novegeo:geographic",
        coordinate_reference_version=1,
        runtime_mode="shared_reference",
        qualification_id="qualification:novegeo:world-boundary:v002",
    )
    assert association.boundary_id == "boundary:novegeo:sovereign"
    assert association.boundary_version == 2
    assert not hasattr(association, "geometry")


def test_p006_7_1_6_boundary_association_preserves_shared_reference_semantics():
    with pytest.raises(ValueError, match="shared_reference"):
        SovereignBoundaryAssociation(
            "country-boundary:novegeo:v002",
            "country:novegeo",
            "boundary:novegeo:sovereign",
            2,
            "crs:novegeo:geographic",
            1,
            "simulation",
        )
