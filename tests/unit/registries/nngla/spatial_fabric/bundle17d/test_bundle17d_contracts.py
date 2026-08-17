import pytest

from registries.nngla.spatial_fabric.bundle17d.contracts import FeatureTypeExtension, MarineSubjectType


def test_bundle17d_subject_types_are_explicit_and_do_not_conflate_route_name_with_route():
    assert {item.value for item in MarineSubjectType} == {
        "MARINE_WATERBODY", "COASTAL_INTERFACE", "MARINE_ANCHOR", "SEA_ROUTE", "MARINE_CONNECTION", "ISLAND_PHYSICAL_STATE",
    }


def test_bundle17d_rejects_nngla_creation_of_natural_physical_geography():
    with pytest.raises(ValueError, match="does not physically create"):
        FeatureTypeExtension(
            feature_type_code="TEST_OCEAN", feature_family_code="HYDROLOGY", canonical_label="Test Ocean",
            geometry_expectation="POLYGON", origin_class="NATURAL", nngla_recognizable=True,
            nngla_creatable=True, nameable=True, supports_history=True, status="ACTIVE",
            effective_from="2026-08-17", effective_to="", description="invalid",
        )
