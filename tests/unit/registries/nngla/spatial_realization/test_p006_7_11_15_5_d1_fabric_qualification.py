from registries.nngla.spatial_realization.contracts import (
    BoundaryConflictDecision,
    BoundaryConflictDecisionKind,
    FaceAssignmentDecision,
    FaceDecisionKind,
)
from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.fabric_qualification import (
    qualify_candidate_fabric,
    qualify_candidate_fabric_postgis,
)
from registries.nngla.spatial_realization.face_assignment import assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import FabricDefectKind, build_atomic_face_set
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope


def decisions(scope, face_set):
    face_decisions=[]
    sibling_ids=[item.subject_id for item in scope.exhaustive_siblings]
    for face in face_set.faces:
        if face.automatically_owned:
            continue
        owner=sorted(face.adjacent_subject_ids or face.historical_owner_ids or tuple(sibling_ids))[0]
        face_decisions.append(FaceAssignmentDecision(
            face.face_id,face.geometry_sha256,owner,FaceDecisionKind.TEST_ONLY_GOVERNANCE_FIXTURE,
            "TEST-ONLY:"+face.face_id[-12:],"Non-authoritative topology convergence fixture.",
        ))
    boundary=[]
    for defect in face_set.defects:
        if defect.kind is FabricDefectKind.SIBLING_OUTSIDE_PARENT and defect.requires_governed_review:
            boundary.append(BoundaryConflictDecision(
                defect.defect_id,defect.geometry_sha256,BoundaryConflictDecisionKind.TEST_ONLY_HIERARCHY_FIXTURE,
                "TEST-ONLY:"+defect.defect_id[-12:],"EXCLUDE_OUTSIDE_QUALIFIED_PARENT",
                "Non-authoritative parent-envelope fixture.",
            ))
    return tuple(face_decisions),tuple(boundary)


def candidate(root):
    scope=resolve_initial_fabric_scope(root)
    face_set=build_atomic_face_set(scope,build_shared_edge_graph(scope))
    f,b=decisions(scope,face_set)
    assignment=assign_atomic_faces(scope,face_set,face_decisions=f,boundary_conflict_decisions=b)
    return scope,face_set,assignment


def test_delivery1_northgate_candidate_is_face_complete_and_ready_for_independent_postgis_exact_validation():
    scope,face_set,assignment=candidate("NG-PLC-000086")
    result=qualify_candidate_fabric(scope,face_set,assignment)
    assert result.prototype_ready
    assert result.complete_sibling_set and result.face_exclusivity and result.shared_face_identity_by_construction
    assert result.candidate_gap_km2==0.0
    assert result.candidate_outside_parent_km2==0.0
    assert result.candidate_positive_overlap_km2==0.0


def test_delivery1_silvermere_candidate_explicitly_excludes_approved_parent_conflict_and_is_prototype_ready():
    scope,face_set,assignment=candidate("NG-PLC-000258")
    result=qualify_candidate_fabric(scope,face_set,assignment)
    assert result.prototype_ready
    assert result.candidate_gap_km2==0.0
    assert result.candidate_outside_parent_km2==0.0
    assert result.candidate_positive_overlap_km2==0.0


class Cursor:
    def __init__(self): self.sql="";self.params=()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self,sql,params): self.sql=sql;self.params=params
    def fetchone(self): return (True,True,True,True,0.0,0.0)


class Connection:
    def __init__(self): self.last=None
    def cursor(self): self.last=Cursor();return self.last


def test_delivery1_postgis_exact_validator_is_select_only_and_checks_required_exact_predicates():
    scope,_,assignment=candidate("NG-PLC-000086")
    connection=Connection()
    result=qualify_candidate_fabric_postgis(connection,scope,assignment)
    sql=connection.last.sql.upper()
    assert result.exact_pass
    assert "ST_COVERS" in sql and "ST_SYMDIFFERENCE" in sql and "ST_ISVALID" in sql
    for prohibited in ("INSERT ","UPDATE ","DELETE ","CREATE ","ALTER ","DROP "):
        assert prohibited not in sql
