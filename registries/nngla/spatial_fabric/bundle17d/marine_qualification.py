"""Bundle 17D New Waters subject-level spatial qualification."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from functools import lru_cache

from registries.nngla.spatial_fabric.bundle17b import derive_containment_qualifications
from registries.nngla.spatial_fabric.coordinate_occurrences import candidate_identity

from .contracts import MarineSpatialQualificationResult, MarineSubjectType
from .feature_type_extensions import effective_feature_type_codes
from .marine_route_types import marine_route_types
from .marine_sources import load_marine_sources, marine_source_findings


def _truth(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _qual(index: int, **kwargs) -> MarineSpatialQualificationResult:
    return MarineSpatialQualificationResult(marine_qualification_id=f"NG-MAR-QUAL-{index:06d}", **kwargs)


@lru_cache(maxsize=1)
def derive_marine_spatial_qualification_results() -> tuple[MarineSpatialQualificationResult, ...]:
    if marine_source_findings():
        raise ValueError("New Waters source family failed immutable source checks")
    data = load_marine_sources()
    waterbodies = data["novegeo_marine_waterbodies_v001.csv"]
    interfaces = data["novegeo_marine_coastal_interfaces_v001.csv"]
    anchors = data["novegeo_marine_route_anchor_points_v001.csv"]
    routes = data["novegeo_sea_route_candidates_v001.csv"]
    vertices = data["novegeo_sea_route_vertices_v001.csv"]
    derivations = data["novegeo_sea_route_derivation_crosswalk_v001.csv"]
    connections = data["novegeo_island_mainland_connections_v001.csv"]
    validations = data["novegeo_marine_route_validation_v001.csv"]
    island_states = data["novegeo_island_physical_state_v001.csv"]

    feature_codes = effective_feature_type_codes()
    route_types = {row.marine_route_type_code: row for row in marine_route_types()}
    containment = {row.coordinate_candidate_id: row for row in derive_containment_qualifications()}
    water_by_id = {row["marine_waterbody_id"]: row for row in waterbodies}
    route_by_id = {row["route_candidate_id"]: row for row in routes}
    anchor_by_id = {row["anchor_id"]: row for row in anchors}
    validation_by_route = {row["route_candidate_id"]: row for row in validations}
    connection_by_id = {row["connection_id"]: row for row in connections}
    state_by_island = {row["island_candidate_id"]: row for row in island_states}
    vertices_by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    derivations_by_route: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in vertices:
        vertices_by_route[row["route_candidate_id"]].append(row)
    for row in derivations:
        derivations_by_route[row["route_candidate_id"]].append(row)

    out: list[MarineSpatialQualificationResult] = []
    idx = 1

    for row in waterbodies:
        feature_ok = row["feature_type"] in feature_codes
        known_geometry_limit = row["geometry_status"] == "COASTAL_INTERFACES_DEFINED_OUTER_MARINE_ENVELOPE_NOT_PRESENT_IN_REPOSITORY"
        status = "PASS_WITH_KNOWN_GEOMETRY_LIMITATION" if feature_ok and known_geometry_limit else "FAIL"
        out.append(_qual(idx,
            subject_type=MarineSubjectType.MARINE_WATERBODY,
            subject_id=row["marine_waterbody_id"],
            marine_waterbody_id=row["marine_waterbody_id"],
            governed_feature_type_code=row["feature_type"],
            marine_route_type_code="",
            source_geometry_status=row["geometry_status"],
            coordinate_qualification_status="NOT_APPLICABLE_OUTER_MARINE_ENVELOPE_ABSENT",
            containment_context=row["relationship_to_novegeo"],
            land_overlap_status="NOT_EVALUABLE_OUTER_MARINE_ENVELOPE_ABSENT",
            source_fidelity_status="PASS",
            derivation_lineage_status="SOURCE_DECLARED",
            naming_status=row["naming_status"],
            sovereignty_assertion_status=row["sovereignty_claim_status"],
            publication_status="FOUNDATION_REFERENCE_NOT_CANONICAL_PERSISTENCE",
            qualification_status=status,
            findings="OUTER_MARINE_ENVELOPE_NOT_IN_REPOSITORY;NO_JURISDICTION_INFERRED" if status != "FAIL" else "WATERBODY_CONTRACT_FAILURE",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    for row in interfaces:
        endpoint_relations = []
        for prefix in ("start", "end"):
            cid = candidate_identity(Decimal(row[f"{prefix}_longitude"]), Decimal(row[f"{prefix}_latitude"]))
            endpoint_relations.append(containment.get(cid))
        good = (
            row["marine_waterbody_id"] in water_by_id
            and all(rel is not None and rel.qualification_status == "PASS" and rel.boundary_relation == "TOUCHES" for rel in endpoint_relations)
            and all(rel.sovereign_part_id == row["land_part_id"] for rel in endpoint_relations if rel is not None)
        )
        reserve = row["future_geographic_feature_reserve"].upper().replace("LONG_BEACH", "BEACH")
        governed = reserve if reserve and reserve in feature_codes else "COASTLINE"
        out.append(_qual(idx,
            subject_type=MarineSubjectType.COASTAL_INTERFACE,
            subject_id=row["marine_interface_id"],
            marine_waterbody_id=row["marine_waterbody_id"],
            governed_feature_type_code=governed,
            marine_route_type_code="",
            source_geometry_status="GOVERNED_COASTAL_INTERFACE_SEGMENT",
            coordinate_qualification_status="PASS" if good else "FAIL",
            containment_context=f"{row['interface_type']}:{row['land_part_id']}",
            land_overlap_status="EXPECTED_LAND_MARINE_BOUNDARY_INTERFACE",
            source_fidelity_status="PASS",
            derivation_lineage_status="SOURCE_BOUNDARY_SEGMENT_LEDGER_LINKED",
            naming_status="NOT_ASSIGNED_BY_INTERFACE",
            sovereignty_assertion_status=water_by_id[row["marine_waterbody_id"]]["sovereignty_claim_status"] if row["marine_waterbody_id"] in water_by_id else "UNKNOWN",
            publication_status="FOUNDATION_REFERENCE_NOT_CANONICAL_PERSISTENCE",
            qualification_status="PASS" if good else "FAIL",
            findings="" if good else "COASTAL_INTERFACE_ENDPOINT_OR_PART_MISMATCH",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    for row in anchors:
        cid = candidate_identity(Decimal(row["longitude"]), Decimal(row["latitude"]))
        rel = containment.get(cid)
        good = (
            row["route_candidate_id"] in route_by_id
            and row["marine_waterbody_id"] in water_by_id
            and row["crs_code"] == "EPSG:4326"
            and rel is not None
            and rel.qualification_status == "PASS"
            and rel.boundary_relation == "TOUCHES"
            and rel.sovereign_part_id == row["sovereign_part_id"]
        )
        out.append(_qual(idx,
            subject_type=MarineSubjectType.MARINE_ANCHOR,
            subject_id=row["anchor_id"],
            marine_waterbody_id=row["marine_waterbody_id"],
            governed_feature_type_code="COASTLINE",
            marine_route_type_code=route_by_id[row["route_candidate_id"]]["connection_type"] if row["route_candidate_id"] in route_by_id else "",
            source_geometry_status="SOURCE_DERIVATIVE_BOUNDARY_VERTEX",
            coordinate_qualification_status="PASS" if good else "FAIL",
            containment_context=f"ON_SOVEREIGN_BOUNDARY:{row['sovereign_part_id']}:{row['anchor_role']}",
            land_overlap_status="BOUNDARY_ENDPOINT_EXPECTED",
            source_fidelity_status="PASS",
            derivation_lineage_status="SOURCE_DERIVATIVE_VERTEX_LINKED",
            naming_status="NOT_APPLICABLE",
            sovereignty_assertion_status=water_by_id[row["marine_waterbody_id"]]["sovereignty_claim_status"] if row["marine_waterbody_id"] in water_by_id else "UNKNOWN",
            publication_status="FOUNDATION_REFERENCE_NOT_CANONICAL_PERSISTENCE",
            qualification_status="PASS" if good else "FAIL",
            findings="" if good else "MARINE_ANCHOR_BOUNDARY_OR_SOURCE_MISMATCH",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    for row in routes:
        route_vertices = sorted(vertices_by_route[row["route_candidate_id"]], key=lambda r: int(r["vertex_sequence"]))
        route_derivations = sorted(derivations_by_route[row["route_candidate_id"]], key=lambda r: int(r["route_vertex_sequence"]))
        validation = validation_by_route.get(row["route_candidate_id"])
        start_anchor = anchor_by_id.get(row["mainland_anchor_id"])
        end_anchor = anchor_by_id.get(row["island_anchor_id"])
        relations = []
        for vertex in route_vertices:
            cid = candidate_identity(Decimal(vertex["longitude"]), Decimal(vertex["latitude"]))
            relations.append(containment.get(cid))
        endpoints_good = (
            len(relations) == 5
            and relations[0] is not None and relations[0].boundary_relation == "TOUCHES"
            and relations[-1] is not None and relations[-1].boundary_relation == "TOUCHES"
            and start_anchor is not None and relations[0].sovereign_part_id == start_anchor["sovereign_part_id"]
            and end_anchor is not None and relations[-1].sovereign_part_id == end_anchor["sovereign_part_id"]
        )
        interiors_good = len(relations) == 5 and all(
            rel is not None and rel.sovereign_land_relation.value == "OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE"
            for rel in relations[1:-1]
        )
        validation_good = validation is not None and all((
            _truth(validation["geometry_valid"]),
            _truth(validation["mainland_anchor_is_source_derivative_vertex"]),
            _truth(validation["island_anchor_is_source_derivative_vertex"]),
            _truth(validation["interior_water_only"]),
            Decimal(validation["land_overlap_length_degrees"]) == 0,
            validation["validation_status"] == "PASSED",
            not _truth(validation["route_name_assigned"]),
        ))
        derivation_good = (
            len(route_vertices) == 5
            and [int(v["vertex_sequence"]) for v in route_vertices] == [1, 2, 3, 4, 5]
            and len(route_derivations) == 5
            and [int(v["route_vertex_sequence"]) for v in route_derivations] == [1, 2, 3, 4, 5]
        )
        naming_independent = not row["route_name_id"] and not row["canonical_route_name"] and row["naming_status"] == "UNNAMED"
        route_type_good = row["connection_type"] in route_types and row["geometry_type"] == route_types[row["connection_type"]].geometry_type_code
        good = endpoints_good and interiors_good and validation_good and derivation_good and naming_independent and route_type_good
        out.append(_qual(idx,
            subject_type=MarineSubjectType.SEA_ROUTE,
            subject_id=row["route_candidate_id"],
            marine_waterbody_id=row["marine_waterbody_id"],
            governed_feature_type_code="",
            marine_route_type_code=row["connection_type"],
            source_geometry_status=f"{row['geometry_type']}:{len(route_vertices)}_VERTICES",
            coordinate_qualification_status="PASS" if endpoints_good and interiors_good else "FAIL",
            containment_context="BOUNDARY_TO_MARINE_INTERIOR_TO_BOUNDARY",
            land_overlap_status="ZERO_LAND_OVERLAP" if validation_good else "FAILED_OR_UNVERIFIED_LAND_OVERLAP",
            source_fidelity_status="PASS",
            derivation_lineage_status="PASS" if derivation_good else "FAIL",
            naming_status=row["naming_status"],
            sovereignty_assertion_status=water_by_id[row["marine_waterbody_id"]]["sovereignty_claim_status"],
            publication_status=row["publication_status"],
            qualification_status="PASS" if good else "FAIL",
            findings="PHYSICAL_ROUTE_QUALIFIED_NAME_INDEPENDENT" if good else "SEA_ROUTE_QUALIFICATION_FAILURE",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    for row in connections:
        route = route_by_id.get(row["route_candidate_id"])
        state = state_by_island.get(row["island_candidate_id"])
        good = (
            row["marine_waterbody_id"] in water_by_id
            and route is not None
            and state is not None
            and route["destination_island_candidate_id"] == row["island_candidate_id"]
            and state["sovereign_part_id"] == row["island_sovereign_part_id"]
            and state["route_connection_id"] == row["connection_id"]
            and row["route_naming_status"] == "UNNAMED"
        )
        out.append(_qual(idx,
            subject_type=MarineSubjectType.MARINE_CONNECTION,
            subject_id=row["connection_id"],
            marine_waterbody_id=row["marine_waterbody_id"],
            governed_feature_type_code="",
            marine_route_type_code=route["connection_type"] if route else "",
            source_geometry_status="ROUTE_REFERENCE",
            coordinate_qualification_status="INHERITS_QUALIFIED_ROUTE" if good else "FAIL",
            containment_context=f"{row['mainland_sovereign_part_id']}->{row['island_sovereign_part_id']}",
            land_overlap_status="INHERITS_ZERO_LAND_OVERLAP_ROUTE" if good else "FAIL",
            source_fidelity_status="PASS",
            derivation_lineage_status="PASS" if good else "FAIL",
            naming_status=row["route_naming_status"],
            sovereignty_assertion_status=water_by_id[row["marine_waterbody_id"]]["sovereignty_claim_status"] if row["marine_waterbody_id"] in water_by_id else "UNKNOWN",
            publication_status="FOUNDATION_REFERENCE_NOT_CANONICAL_PERSISTENCE",
            qualification_status="PASS" if good else "FAIL",
            findings="" if good else "MARINE_CONNECTION_LINEAGE_FAILURE",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    for row in island_states:
        connection = connection_by_id.get(row["route_connection_id"])
        good = (
            connection is not None
            and connection["island_candidate_id"] == row["island_candidate_id"]
            and connection["island_sovereign_part_id"] == row["sovereign_part_id"]
            and row["boundary_version"] == "2"
            and _truth(row["is_current"])
            and row["physical_state"] == "EXPOSED"
            and row["naming_status"] == "UNNAMED"
        )
        out.append(_qual(idx,
            subject_type=MarineSubjectType.ISLAND_PHYSICAL_STATE,
            subject_id=row["island_state_record_id"],
            marine_waterbody_id=connection["marine_waterbody_id"] if connection else "NG-MAR-WAT-000001",
            governed_feature_type_code="ISLAND",
            marine_route_type_code=route_by_id[connection["route_candidate_id"]]["connection_type"] if connection and connection["route_candidate_id"] in route_by_id else "",
            source_geometry_status="QUALIFIED_OFFSHORE_ISLAND_POLYGON_PRESENT_IN_BOUNDARY_V002",
            coordinate_qualification_status="BOUNDARY_POLYGON_STATE_REFERENCE",
            containment_context=f"OFFSHORE_ISLAND:{row['sovereign_part_id']}",
            land_overlap_status="ISLAND_LAND_EXPECTED",
            source_fidelity_status="PASS",
            derivation_lineage_status="PASS" if good else "FAIL",
            naming_status=row["naming_status"],
            sovereignty_assertion_status=water_by_id[connection["marine_waterbody_id"]]["sovereignty_claim_status"] if connection else "NOT_ASSERTED_BY_THIS_RECORD",
            publication_status="FOUNDATION_REFERENCE_NOT_CANONICAL_PERSISTENCE",
            qualification_status="PASS" if good else "FAIL",
            findings="" if good else "ISLAND_STATE_CONNECTION_FAILURE",
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
        idx += 1

    if len(out) != 49:
        raise ValueError(f"Bundle 17D expected 49 subject-level qualifications, got {len(out)}")
    return tuple(out)


def marine_qualification_findings(rows: tuple[MarineSpatialQualificationResult, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_marine_spatial_qualification_results()
    return tuple(f"{row.subject_type.value}:{row.subject_id}:{row.findings}" for row in current if row.qualification_status == "FAIL")


__all__ = ["derive_marine_spatial_qualification_results", "marine_qualification_findings"]
