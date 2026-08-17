from decimal import Decimal
from registries.nngla.spatial_fabric.bundle17h import (
    form_site_candidate, form_structure_site_reference, load_house_crosswalk,
    load_house_site_requirements, site_meets_house_requirement,
)
from registries.nngla.spatial_fabric.bundle17h.artifacts import artifact_paths


def test_house_catalogue_bridge_preserves_120_designs_and_governed_place_lineage():
    paths = artifact_paths()
    crosswalk = load_house_crosswalk(paths["house_crosswalk"])
    requirements = load_house_site_requirements(paths["house_site_requirements"])
    assert len(crosswalk) == 120 == len(requirements)
    assert {row.legacy_place_registry_reference for row in crosswalk} == {"novegeo_places_registry_v001_700.csv"}
    assert {row.governed_place_dataset_id for row in crosswalk} == {"dataset:novegeo:places:v001:700"}
    assert {row.current_place_source for row in crosswalk} == {"settlement_name_catalogue.csv"}
    assert len({row.primary_compatible_terrain_zone for row in requirements}) == 8


def test_site_requirement_checks_only_spatial_site_facts_not_house_cost_or_residence():
    requirement = load_house_site_requirements(artifact_paths()["house_site_requirements"])[0]
    good_ground = requirement.suitable_ground_conditions[0]
    assert site_meets_house_requirement(requirement, terrain_zone=requirement.primary_compatible_terrain_zone, plot_area_sqm=requirement.minimum_plot_area_sqm, site_slope_percent=Decimal("0"), ground_condition=good_ground)
    assert not site_meets_house_requirement(requirement, terrain_zone=requirement.primary_compatible_terrain_zone, plot_area_sqm=Decimal("1"), site_slope_percent=Decimal("0"), ground_condition=good_ground)


def test_structure_reference_keeps_structure_owned_by_external_registry():
    site = form_site_candidate(place_id="NG-PLC-000001", source_reference="test:site")
    ref = form_structure_site_reference(site, structure_reference_type_code="HOUSE", external_registry_code="FUTURE_CONSTRUCTION_REGISTRY", external_structure_reference="house:future:1", effective_from="2026-08-17", source_reference="test:bridge")
    assert ref.external_registry_code == "FUTURE_CONSTRUCTION_REGISTRY"
    assert ref.site_id == site.site_id
