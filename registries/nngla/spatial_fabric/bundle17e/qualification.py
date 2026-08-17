"""Bundle 17E persistence qualification over locked Bundle 17A-17D evidence."""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

from registries.nngla.spatial_fabric.bundle17d import bundle17d_is_qualified

from ._shared import (
    CONFLICT_QUALIFICATION_PATH,
    CONTAINMENT_PATH,
    EFFECT_SCOPE,
    ENVIRONMENT_BINDINGS_PATH,
    OCCURRENCE_CROSSWALK_PATH,
    OCCUPANCY_RELATIONSHIPS_PATH,
    PRECISION_PATH,
    SOURCE_FIDELITY_PATH,
    TOPOLOGY_QUALIFICATION_PATH,
    csv_rows,
)
from .canonical import canonical_by_candidate, coordinate_candidate_rows
from .contracts import PersistenceQualificationResult, SpatialMigrationAction
from .geometry import derive_effective_dated_assignments, geometry_by_candidate


def _all_pass(values: list[str], allowed: set[str]) -> bool:
    return bool(values) and all(value in allowed for value in values)


@lru_cache(maxsize=1)
def derive_persistence_qualifications() -> tuple[PersistenceQualificationResult, ...]:
    candidates = coordinate_candidate_rows()
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    assignments = {row.subject_id: row for row in derive_effective_dated_assignments()}

    occurrence_candidate = {
        row["coordinate_occurrence_id"]: row["coordinate_candidate_id"] for row in csv_rows(OCCURRENCE_CROSSWALK_PATH)
    }
    fidelity: dict[str, list[str]] = defaultdict(list)
    for row in csv_rows(SOURCE_FIDELITY_PATH):
        candidate_id = occurrence_candidate[row["coordinate_occurrence_id"]]
        fidelity[candidate_id].append(row["fidelity_status"])

    precision: dict[str, list[str]] = defaultdict(list)
    for row in csv_rows(PRECISION_PATH):
        precision[row["coordinate_candidate_id"]].append(row["precision_status"])

    containment = {row["coordinate_candidate_id"]: row for row in csv_rows(CONTAINMENT_PATH)}
    environment = {row["coordinate_candidate_id"]: row for row in csv_rows(ENVIRONMENT_BINDINGS_PATH)}
    topology = {row["spatial_reference_id"]: row for row in csv_rows(TOPOLOGY_QUALIFICATION_PATH)}

    occupancy_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in csv_rows(OCCUPANCY_RELATIONSHIPS_PATH):
        occupancy_by_candidate[row["coordinate_candidate_id"]].append(row)
    conflict_by_evidence = {
        row["relationship_evidence_id"]: row for row in csv_rows(CONFLICT_QUALIFICATION_PATH)
    }

    out: list[PersistenceQualificationResult] = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = candidate["coordinate_candidate_id"]
        crosswalk = crosswalks[candidate_id]
        geometry = geometries[candidate_id]
        assignment = assignments[crosswalk.canonical_spatial_point_id]

        source_verified = _all_pass(fidelity[candidate_id], {"PASS"})
        precision_valid = _all_pass(precision[candidate_id], {"PASS"})
        crs_valid = candidate["governed_crs_code"] == "NG-CRS-EPSG4326"
        containment_row = containment.get(candidate_id)
        containment_valid = bool(containment_row and containment_row["qualification_status"] == "PASS")
        map_reconciled = bool(containment_row and containment_row["map_extent_status"] == "WITHIN_GOVERNED_EXTENT")
        coordinate_valid = source_verified and precision_valid and crs_valid and containment_valid and map_reconciled

        environment_row = environment.get(candidate_id)
        if environment_row:
            environment_resolved = environment_row["environment_resolution_status"] == "PASS"
            environment_applicability = "APPLICABLE_REFERENCE_FABRIC_POINT"
            cell_status = topology.get(environment_row["spatial_cell_id"], {}).get("topology_status")
            grid_status = topology.get(environment_row["major_grid_id"], {}).get("topology_status")
            topology_valid = cell_status == "PASS" and grid_status == "PASS"
            topology_applicability = "APPLICABLE_REFERENCE_CELL_AND_MAJOR_GRID"
        else:
            environment_resolved = True
            environment_applicability = "NOT_APPLICABLE_NO_ENVIRONMENT_BINDING_REQUIRED"
            topology_valid = True
            topology_applicability = "NOT_APPLICABLE_FREE_COORDINATE_NOT_A_REFERENCE_CELL"

        occupancy = occupancy_by_candidate.get(candidate_id, [])
        if occupancy:
            conflict_rows = [conflict_by_evidence[row["relationship_evidence_id"]] for row in occupancy]
            conflict_free = all(row["qualification_status"] in {"PASS", "PASS_WITH_DEFERRED_GEOMETRY"} for row in conflict_rows)
            conflict_applicability = "APPLICABLE_REFERENCE_POINT_RELATION_FULL_EXTENT_DEFERRED"
        else:
            conflict_free = True
            conflict_applicability = "NOT_APPLICABLE_NO_ASSERTED_OCCUPANCY_RELATION"

        canonical_id_stable = crosswalk.canonical_spatial_point_id == assignment.subject_id
        geometry_assignment_valid = geometry.canonical_spatial_point_id == assignment.subject_id and geometry.geometry_id == assignment.geometry_id
        crosswalk_valid = crosswalk.status == "QUALIFIED_FOR_PERSISTENCE"
        effective_dating_valid = assignment.assignment_status == "QUALIFIED_FOR_PERSISTENCE" and not assignment.effective_to

        checks = (
            source_verified, coordinate_valid, map_reconciled, crs_valid, precision_valid, containment_valid,
            topology_valid, environment_resolved, conflict_free, canonical_id_stable, geometry_assignment_valid,
            crosswalk_valid, effective_dating_valid,
        )
        status = "PASS" if all(checks) else "FAIL"
        findings = "" if status == "PASS" else "FAIL_CLOSED_PERSISTENCE_PRECONDITION"
        out.append(PersistenceQualificationResult(
            persistence_qualification_id=f"NG-SPPERSIST-{index:07d}",
            coordinate_candidate_id=candidate_id,
            canonical_spatial_point_id=crosswalk.canonical_spatial_point_id,
            geometry_id=geometry.geometry_id,
            migration_action=SpatialMigrationAction.INSERT_NEW,
            source_verified=source_verified,
            coordinate_valid=coordinate_valid,
            map_reconciled=map_reconciled,
            crs_valid=crs_valid,
            precision_valid=precision_valid,
            containment_valid=containment_valid,
            topology_valid=topology_valid,
            topology_applicability=topology_applicability,
            environment_resolved=environment_resolved,
            environment_applicability=environment_applicability,
            conflict_free=conflict_free,
            conflict_applicability=conflict_applicability,
            canonical_id_stable=canonical_id_stable,
            geometry_assignment_valid=geometry_assignment_valid,
            crosswalk_valid=crosswalk_valid,
            effective_dating_valid=effective_dating_valid,
            qualification_status=status,
            findings=findings,
            runtime_effect_scope=EFFECT_SCOPE,
        ))
    return tuple(out)


def persistence_findings(rows: tuple[PersistenceQualificationResult, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_persistence_qualifications()
    return tuple(f"{row.coordinate_candidate_id}:{row.findings}" for row in current if row.qualification_status != "PASS")


def bundle17e_is_qualified() -> bool:
    rows = derive_persistence_qualifications()
    return bundle17d_is_qualified() and len(rows) == 2411 and not persistence_findings(rows)


__all__ = ["derive_persistence_qualifications", "persistence_findings", "bundle17e_is_qualified"]
