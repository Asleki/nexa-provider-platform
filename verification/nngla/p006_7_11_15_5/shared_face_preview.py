#!/usr/bin/env python3
"""Read-only Delivery-1 parent-scoped shared-face prototype preview."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from registries.nngla.spatial_realization.contracts import (
    BoundaryConflictDecision,
    BoundaryConflictDecisionKind,
    FaceAssignmentDecision,
    FaceDecisionKind,
)
from registries.nngla.spatial_realization.face_polygonization import FabricDefectKind
from registries.nngla.spatial_realization.shared_face_preview import (
    build_read_only_shared_face_preview,
    preview_payload,
)


def parser() -> argparse.ArgumentParser:
    value=argparse.ArgumentParser(description=__doc__)
    value.add_argument("--root",required=True,help="Canonical NG-PLC major-city root")
    value.add_argument("--material-rule",action="append",default=[],help="Known material rule code; repeat as needed")
    value.add_argument("--decisions",default="",help="Optional explicit governed/test decision JSON")
    value.add_argument("--output",default="",help="Optional report JSON path")
    value.add_argument("--decision-template",default="",help="Optional path for unresolved decision template JSON")
    return value


def _load_decisions(path_text: str):
    if not path_text:
        return (),()
    payload=json.loads(Path(path_text).read_text(encoding="utf-8"))
    faces=tuple(FaceAssignmentDecision(
        face_id=str(row["faceId"]),
        face_geometry_sha256=str(row["faceGeometrySha256"]),
        owner_subject_id=str(row["ownerSubjectId"]),
        decision_kind=FaceDecisionKind(str(row["decisionKind"])),
        decision_reference=str(row["decisionReference"]),
        rationale=str(row["rationale"]),
    ) for row in payload.get("faceDecisions",[]))
    boundaries=tuple(BoundaryConflictDecision(
        defect_id=str(row["defectId"]),
        defect_geometry_sha256=str(row["defectGeometrySha256"]),
        decision_kind=BoundaryConflictDecisionKind(str(row["decisionKind"])),
        decision_reference=str(row["decisionReference"]),
        action=str(row["action"]),
        rationale=str(row["rationale"]),
    ) for row in payload.get("boundaryConflictDecisions",[]))
    return faces,boundaries


def _decision_template(preview):
    sibling_ids=[item.subject_id for item in preview.scope.exhaustive_siblings]
    faces=[]
    for face in preview.face_set.faces:
        if face.automatically_owned:
            continue
        faces.append({
            "faceId":face.face_id,
            "faceGeometrySha256":face.geometry_sha256,
            "classification":face.classification.value,
            "areaKm2":face.area_km2,
            "adjacentSubjectIds":list(face.adjacent_subject_ids),
            "historicalOwnerIds":list(face.historical_owner_ids),
            "allowedOwnerSubjectIds":sibling_ids,
            "ownerSubjectId":"",
            "decisionKind":"GOVERNED_REVIEW",
            "decisionReference":"",
            "rationale":"",
        })
    boundaries=[]
    for defect in preview.face_set.defects:
        if defect.kind in {
            FabricDefectKind.SIBLING_OUTSIDE_PARENT,
            FabricDefectKind.INDIVIDUAL_SIBLING_OUTSIDE_PARENT,
        } and defect.requires_governed_review:
            boundaries.append({
                "defectId":defect.defect_id,
                "defectGeometrySha256":defect.geometry_sha256,
                "kind":defect.kind.value,
                "areaKm2":defect.area_km2,
                "adjacentSubjectIds":list(defect.adjacent_subject_ids),
                "sourceSubjectIds":list(defect.source_subject_ids),
                "decisionKind":"GOVERNED_REVIEW",
                "decisionReference":"",
                "action":"EXCLUDE_OUTSIDE_QUALIFIED_PARENT",
                "rationale":"",
            })
    return {
        "scopeFingerprint":preview.scope.fingerprint,
        "faceSetSha256":preview.face_set.face_set_sha256,
        "notice":"Template only. Blank choices are not authority. Material ownership requires an explicit NNGLA decision.",
        "faceDecisions":faces,
        "boundaryConflictDecisions":boundaries,
    }


def main(argv=None) -> int:
    args=parser().parse_args(argv)
    faces,boundaries=_load_decisions(args.decisions)
    preview=build_read_only_shared_face_preview(
        args.root,
        material_rule_codes=args.material_rule,
        face_decisions=faces,
        boundary_conflict_decisions=boundaries,
    )
    payload=preview_payload(preview)
    encoded=json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)
    print(encoded)
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded+"\n",encoding="utf-8")
    if args.decision_template:
        path=Path(args.decision_template);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(_decision_template(preview),indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0 if preview.qualification is not None and preview.qualification.prototype_ready else 2


if __name__=="__main__":
    raise SystemExit(main())
