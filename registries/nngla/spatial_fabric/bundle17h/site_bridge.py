"""Bundle 17H addressable-site, external structure and house requirement bridge."""
from __future__ import annotations

from decimal import Decimal

from ._shared import HOUSE_CATALOGUE_SHA256, csv_rows, stable_id
from .contracts import (
    AddressableSiteCandidate, HouseCatalogueCrosswalk, HouseDesignSiteRequirement,
    SiteLifecycleStage, StructureSiteReference, SiteAddressAssignmentCandidate,
)


def form_site_candidate(
    *, place_id: str = "", administrative_area_id: str = "", parcel_id: str = "", geometry_id: str = "",
    road_id: str = "", road_segment_id: str = "", lifecycle_stage: SiteLifecycleStage | str = SiteLifecycleStage.CANDIDATE,
    runtime_mode: str = "simulation", source_reference: str,
) -> AddressableSiteCandidate:
    site_id = stable_id(
        "site:nngla:", place_id, administrative_area_id, parcel_id, geometry_id, road_id, road_segment_id,
        str(lifecycle_stage), runtime_mode, source_reference,
    )
    return AddressableSiteCandidate(
        site_id=site_id, place_id=place_id, administrative_area_id=administrative_area_id, parcel_id=parcel_id,
        geometry_id=geometry_id, road_id=road_id, road_segment_id=road_segment_id,
        lifecycle_stage=lifecycle_stage, runtime_mode=runtime_mode, source_reference=source_reference,
    )


def form_structure_site_reference(
    site: AddressableSiteCandidate, *, structure_reference_type_code: str, external_registry_code: str,
    external_structure_reference: str, effective_from: str, source_reference: str,
) -> StructureSiteReference:
    identity = stable_id("structsite:nngla:", site.site_id, external_registry_code, external_structure_reference, effective_from)
    return StructureSiteReference(
        structure_site_reference_id=identity, site_id=site.site_id,
        structure_reference_type_code=structure_reference_type_code, external_registry_code=external_registry_code,
        external_structure_reference=external_structure_reference, effective_from=effective_from, effective_to="",
        reference_status="PROPOSED", source_reference=source_reference,
    )


def form_site_address_assignment_candidate(site: AddressableSiteCandidate, reservation, *, source_reference: str) -> SiteAddressAssignmentCandidate:
    if reservation.site_id != site.site_id:
        raise ValueError("address reservation and site assignment must reference the same site")
    identity = stable_id("siteaddr:nngla:", site.site_id, reservation.reservation_id, reservation.reserved_address_id)
    return SiteAddressAssignmentCandidate(
        assignment_candidate_id=identity, site_id=site.site_id, address_reservation_id=reservation.reservation_id,
        address_id=reservation.reserved_address_id, assignment_status="CANDIDATE", runtime_mode=site.runtime_mode,
        source_reference=source_reference,
    )


def load_house_crosswalk(path) -> tuple[HouseCatalogueCrosswalk, ...]:
    return tuple(HouseCatalogueCrosswalk(
        citizen_house_design_id=row["citizen_house_design_id"], citizen_house_design_code=row["citizen_house_design_code"],
        legacy_place_registry_reference=row["legacy_place_registry_reference"], governed_place_dataset_id=row["governed_place_dataset_id"],
        current_place_source=row["current_place_source"], source_catalogue=row["source_catalogue"],
        source_catalogue_sha256=row["source_catalogue_sha256"], crosswalk_status=row["crosswalk_status"],
    ) for row in csv_rows(path))


def load_house_site_requirements(path) -> tuple[HouseDesignSiteRequirement, ...]:
    return tuple(HouseDesignSiteRequirement(
        citizen_house_design_id=row["citizen_house_design_id"], citizen_house_design_code=row["citizen_house_design_code"],
        primary_compatible_terrain_zone=row["primary_compatible_terrain_zone"],
        compatible_terrain_zones=tuple(filter(None, row["compatible_terrain_zones"].split("|"))),
        minimum_plot_area_sqm=Decimal(row["minimum_plot_area_sqm"]),
        suitable_ground_conditions=tuple(filter(None, row["suitable_ground_conditions"].split("|"))),
        unsuitable_ground_conditions=tuple(filter(None, row["unsuitable_ground_conditions"].split("|"))),
        maximum_site_slope_percent=Decimal(row["maximum_site_slope_percent"]),
        minimum_floor_clearance_mm=int(row["minimum_floor_clearance_mm"]),
        flood_resilience_level=row["flood_resilience_level"], wind_resistance_level=row["wind_resistance_level"],
        drainage_requirement=row["drainage_requirement"], site_inspection_requirement=row["site_inspection_requirement"],
        physical_property_id_issue_stage=row["physical_property_id_issue_stage"], source_catalogue_sha256=row["source_catalogue_sha256"],
    ) for row in csv_rows(path))


def site_meets_house_requirement(
    requirement: HouseDesignSiteRequirement, *, terrain_zone: str, plot_area_sqm: Decimal | int | str,
    site_slope_percent: Decimal | int | str, ground_condition: str,
) -> bool:
    return (
        terrain_zone in requirement.compatible_terrain_zones
        and Decimal(str(plot_area_sqm)) >= requirement.minimum_plot_area_sqm
        and Decimal(str(site_slope_percent)) <= requirement.maximum_site_slope_percent
        and ground_condition in requirement.suitable_ground_conditions
        and ground_condition not in requirement.unsuitable_ground_conditions
    )


__all__ = [
    "form_site_candidate", "form_structure_site_reference", "form_site_address_assignment_candidate",
    "load_house_crosswalk", "load_house_site_requirements", "site_meets_house_requirement", "HOUSE_CATALOGUE_SHA256",
]
