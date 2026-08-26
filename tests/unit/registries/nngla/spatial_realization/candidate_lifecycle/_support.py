from shapely import from_wkb

from registries.nngla.spatial_realization.contracts import (
    BoundaryConflictDecision,
    BoundaryConflictDecisionKind,
    FaceAssignmentDecision,
    FaceDecisionKind,
)
from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_assignment import assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import build_atomic_face_set
from registries.nngla.spatial_realization.fabric_qualification import qualify_candidate_fabric
from registries.nngla.spatial_realization.fabric_scope import build_recursive_child_scope, resolve_initial_fabric_scope
from registries.nngla.spatial_realization.shared_face_preview import SharedFacePrototypePreview


def governed_decisions(scope, face_set):
    sibling_ids = tuple(sorted(item.subject_id for item in scope.exhaustive_siblings))
    face_decisions=[]
    for face in face_set.faces:
        if face.automatically_owned:
            continue
        eligible=tuple(sorted(set(face.adjacent_subject_ids or face.historical_owner_ids or sibling_ids)))
        owner=next((value for value in eligible if value in sibling_ids), sibling_ids[0])
        face_decisions.append(FaceAssignmentDecision(
            face_id=face.face_id,
            face_geometry_sha256=face.geometry_sha256,
            owner_subject_id=owner,
            decision_kind=FaceDecisionKind.GOVERNED_REVIEW,
            decision_reference="NNGLA-D2-FACE:"+face.face_id[-20:],
            rationale="Explicit governed Delivery-2 test authority decision.",
        ))
    boundary=[]
    for defect in face_set.defects:
        if defect.requires_governed_review and defect.kind.value in {"SIBLING_OUTSIDE_PARENT","INDIVIDUAL_SIBLING_OUTSIDE_PARENT"}:
            boundary.append(BoundaryConflictDecision(
                defect_id=defect.defect_id,
                defect_geometry_sha256=defect.geometry_sha256,
                decision_kind=BoundaryConflictDecisionKind.GOVERNED_REVIEW,
                decision_reference="NNGLA-D2-BOUNDARY:"+defect.defect_id[-20:],
                action="EXCLUDE_OUTSIDE_QUALIFIED_PARENT",
                rationale="Explicit governed Delivery-2 hierarchy decision.",
            ))
    return tuple(face_decisions),tuple(boundary)


def assigned_preview(root="NG-PLC-000086", *, material_rule_codes=(), overrides=None, scope=None):
    scope=scope or resolve_initial_fabric_scope(root,material_rule_codes=material_rule_codes)
    graph=build_shared_edge_graph(scope,geometry_overrides=overrides)
    faces=build_atomic_face_set(scope,graph,geometry_overrides=overrides)
    fd,bd=governed_decisions(scope,faces)
    assignment=assign_atomic_faces(scope,faces,face_decisions=fd,boundary_conflict_decisions=bd,geometry_overrides=overrides)
    qual=qualify_candidate_fabric(scope,faces,assignment,geometry_overrides=overrides)
    preview=SharedFacePrototypePreview(scope,graph,faces,assignment,qual,qual.status)
    return preview,fd,bd


def unresolved_preview(root="NG-PLC-000086", *, material_rule_codes=()):
    from registries.nngla.spatial_realization.shared_face_preview import build_read_only_shared_face_preview
    return build_read_only_shared_face_preview(root,material_rule_codes=material_rule_codes)


def nyara_and_silvermere():
    region,fd,bd=assigned_preview("NG-PLC-000258",material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED","CITY_DISTRICT_OVERSHOOT"))
    parent=region.assignment.candidate_by_subject["NG-ADM-000078"]
    parent_geom=from_wkb(bytes.fromhex(parent.geometry_wkb_hex))
    child_scope=build_recursive_child_scope(region.scope,"NG-ADM-000078",qualified_parent_geometry_sha256=parent.geometry_sha256,qualified_parent_candidate_id=parent.candidate_id)
    child,cfd,cbd=assigned_preview(scope=child_scope,overrides={"NG-ADM-000078":parent_geom})
    return region,fd,bd,parent,child,cfd,cbd


def bound_governance(preview, face_decisions, boundary_decisions, *, reviewer_actor_id="reviewer", approver_actor_id="approver", runtime_mode="production", parent_candidate_id="", parent_candidate_geometry_sha256=""):
    from registries.nngla.spatial_realization.candidate_lifecycle.governance import bind_governance_decisions
    from registries.nngla.spatial_realization.candidate_lifecycle.package import candidate_run_identity
    run_id,_=candidate_run_identity(
        preview,
        runtime_mode=runtime_mode,
        parent_candidate_id=parent_candidate_id,
        parent_candidate_geometry_sha256=parent_candidate_geometry_sha256,
    )
    return bind_governance_decisions(
        fabric_run_id=run_id,
        scope_fingerprint=preview.scope.fingerprint,
        face_decisions=tuple(face_decisions),
        boundary_decisions=tuple(boundary_decisions),
        reviewer_actor_id=reviewer_actor_id,
        approver_actor_id=approver_actor_id,
        runtime_mode=runtime_mode,
    )
