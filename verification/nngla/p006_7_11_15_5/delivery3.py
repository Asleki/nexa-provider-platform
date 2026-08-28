#!/usr/bin/env python3
"""P006.7.11.15.5 Delivery 3 R1 CITY qualification/authority/publication CLI."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from registries.nngla.spatial_realization.authority_adoption import (
    CandidateSourceMode,
    CityQualificationReceipt,
    CityQualificationStatus,
    GovernedAdministrativeAuthorityService,
    PostgreSQLAdministrativeAuthorityRepository,
    PostgreSQLCityFeatureQualifier,
    PostgreSQLCityPublicationRepository,
    PrecisionMode,
    PrecisionPolicy,
    SOURCE_EXACT_PRECISION,
)
from registries.nngla.spatial_realization.source import city_roots
from verification.nngla.p006_7_11_15_5.common import connect_postgresql, effective_date, write_json

CITY_IDS = tuple(root.administrative_area_id for root in city_roots())


def _require_execute(args) -> None:
    if not getattr(args, "execute", False):
        raise SystemExit("REFUSED: --execute is required for Delivery-3 database writes")


def _precision_policy(args) -> PrecisionPolicy:
    if args.precision_grid_degrees is None:
        return SOURCE_EXACT_PRECISION
    if not args.precision_policy_id or not args.precision_evidence_reference:
        raise SystemExit("governed precision requires --precision-policy-id and --precision-evidence-reference")
    return PrecisionPolicy(
        policy_id=args.precision_policy_id,
        mode=PrecisionMode.GOVERNED_COMMON_PRECISION,
        grid_size_degrees=float(args.precision_grid_degrees),
        evidence_reference=args.precision_evidence_reference,
    )


def _receipt_payload(receipt: CityQualificationReceipt) -> dict[str, object]:
    payload = dict(receipt.material())
    payload["delivery"] = "P006.7.11.15.5-DELIVERY3-R1"
    payload["featureQualificationStatus"] = "FEATURE_QUALIFIED" if receipt.feature_qualified else "FEATURE_REJECTED"
    payload["fabricCompletenessStatus"] = "NOT_ASSESSED"
    payload["publicationEligible"] = False
    payload["databaseMutation"] = False
    return payload


def _load_receipt(path: str) -> CityQualificationReceipt:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    def req(name):
        if name not in payload:
            raise SystemExit(f"qualification receipt missing field: {name}")
        return payload[name]
    return CityQualificationReceipt(
        qualification_id=req("qualification_id"),
        city_administrative_area_id=req("city_administrative_area_id"),
        root_place_id=req("root_place_id"),
        candidate_source_mode=CandidateSourceMode(req("candidate_source_mode")),
        candidate_id=req("candidate_id"),
        raw_candidate_geometry_sha256=req("raw_candidate_geometry_sha256"),
        evaluated_candidate_geometry_sha256=req("evaluated_candidate_geometry_sha256"),
        source_geometry_sha256=req("source_geometry_sha256"),
        source_dataset_id=req("source_dataset_id"),
        source_dataset_version=req("source_dataset_version"),
        source_path_reference=req("source_path_reference"),
        fabric_run_id=payload.get("fabric_run_id", ""),
        package_sha256=payload.get("package_sha256", ""),
        validation_parent_id=req("validation_parent_id"),
        parent_evidence_kind=req("parent_evidence_kind"),
        parent_evidence_id=req("parent_evidence_id"),
        raw_parent_geometry_sha256=req("raw_parent_geometry_sha256"),
        evaluated_parent_geometry_sha256=req("evaluated_parent_geometry_sha256"),
        parent_qualification_reference=req("parent_qualification_reference"),
        parent_source_path_reference=req("parent_source_path_reference"),
        peer_evidence_digest=req("peer_evidence_digest"),
        precision_policy_id=req("precision_policy_id"),
        precision_policy_sha256=req("precision_policy_sha256"),
        precision_mode=PrecisionMode(req("precision_mode")),
        precision_grid_size_degrees=payload.get("precision_grid_size_degrees"),
        precision_evidence_reference=req("precision_evidence_reference"),
        valid_geometry=bool(req("valid_geometry")),
        polygonal=bool(req("polygonal")),
        non_empty=bool(req("non_empty")),
        srid_correct=bool(req("srid_correct")),
        parent_evidence_valid=bool(req("parent_evidence_valid")),
        city_covered_by_parent=bool(req("city_covered_by_parent")),
        raw_area_outside_parent_m2=float(req("raw_area_outside_parent_m2")),
        area_outside_parent_m2=float(req("area_outside_parent_m2")),
        raw_positive_city_peer_overlap_m2=float(req("raw_positive_city_peer_overlap_m2")),
        positive_city_peer_overlap_m2=float(req("positive_city_peer_overlap_m2")),
        raw_positive_municipality_overlap_m2=float(req("raw_positive_municipality_overlap_m2")),
        positive_municipality_overlap_m2=float(req("positive_municipality_overlap_m2")),
        reference_point_covered=bool(req("reference_point_covered")),
        unresolved_city_affecting_defect_count=int(req("unresolved_city_affecting_defect_count")),
        numerical_residue=bool(req("numerical_residue")),
        source_provenance_bound=bool(req("source_provenance_bound")),
        qualifier_actor_id=req("qualifier_actor_id"),
        runtime_mode=req("runtime_mode"),
        status=CityQualificationStatus(req("status")),
        failed_predicates=tuple(payload.get("failed_predicates", ())),
        database_mutation=bool(payload.get("database_mutation", False)),
        qualification_sha256=req("qualification_sha256"),
    )


def _status(connection, city_ids: tuple[str, ...]) -> dict[str, object]:
    placeholders = ",".join(["%s"] * len(city_ids))
    with connection.cursor() as cur:
        cur.execute(
            f"""SELECT a.administrative_area_id,a.canonical_name,a.boundary_status,a.lifecycle_status_code,a.geometry_reference,
                       q.qualification_id,q.feature_qualification_status,
                       ass.assignment_id,ass.assignment_status,
                       leg.legalization_id,leg.decision_status,
                       pub.publication_id,proj.projection_id
                FROM geography.nngla_administrative_area a
                LEFT JOIN geography.nngla_administrative_geometry_assignment ass
                  ON ass.administrative_area_id=a.administrative_area_id AND ass.assignment_status='EFFECTIVE' AND ass.effective_to IS NULL
                LEFT JOIN geography.nngla_city_feature_qualification q ON q.qualification_id=ass.qualification_id
                LEFT JOIN geography.nngla_administrative_legalization_decision leg
                  ON leg.assignment_id=ass.assignment_id AND leg.decision_status='LEGALIZED'
                LEFT JOIN geography.nngla_publication_record pub
                  ON pub.subject_id=a.administrative_area_id AND pub.geometry_id=a.geometry_reference
                 AND pub.runtime_mode='production' AND pub.visibility='PUBLIC' AND pub.decision='PUBLISHED'
                LEFT JOIN geography.nngla_spatial_read_projection_v1 proj
                  ON proj.subject_id=a.administrative_area_id AND proj.geometry_id=a.geometry_reference
                 AND proj.runtime_mode='production' AND proj.visibility='PUBLIC' AND proj.publication_reference=pub.publication_id
                WHERE a.administrative_area_id IN ({placeholders})
                ORDER BY a.administrative_area_id""",
            city_ids,
        )
        rows = list(cur.fetchall())
    items = []
    for r in rows:
        items.append({
            "administrativeAreaId":str(r[0]),"displayName":str(r[1]),"boundaryStatus":str(r[2]),
            "lifecycleStatus":str(r[3]),"geometryId":str(r[4]) if r[4] else None,
            "qualificationId":str(r[5]) if r[5] else None,"featureQualificationStatus":str(r[6]) if r[6] else None,
            "assignmentId":str(r[7]) if r[7] else None,"assignmentStatus":str(r[8]) if r[8] else None,
            "legalizationId":str(r[9]) if r[9] else None,"legalizationStatus":str(r[10]) if r[10] else None,
            "publicationId":str(r[11]) if r[11] else None,"projectionId":str(r[12]) if r[12] else None,
            "publicationEligible":bool(r[6]=="FEATURE_QUALIFIED" and r[8]=="EFFECTIVE" and r[10]=="LEGALIZED"),
            "publicCityReady":bool(r[11] and r[12]),
        })
    return {"delivery":"P006.7.11.15.5-DELIVERY3-R1","items":items,"count":len(items),"databaseMutation":False}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--output", default="", help="Optional JSON output path")
    commands = root.add_subparsers(dest="command", required=True)

    p = commands.add_parser("qualify-city", help="SELECT-only exact qualification for one CITY")
    p.add_argument("--city-id", required=True, choices=CITY_IDS)
    p.add_argument("--qualifier", required=True)
    p.add_argument("--candidate-source", choices=("frozen","delivery2"), default="frozen")
    p.add_argument("--fabric-run-id", default="")
    p.add_argument("--precision-grid-degrees", type=float, default=None)
    p.add_argument("--precision-policy-id", default="")
    p.add_argument("--precision-evidence-reference", default="")

    p = commands.add_parser("adopt-city", help="Re-verify a passing receipt then adopt one CITY authority")
    p.add_argument("--qualification-receipt", required=True)
    p.add_argument("--effective-date", required=True)
    p.add_argument("--submitter", required=True); p.add_argument("--approver", required=True)
    p.add_argument("--decision-reference", required=True); p.add_argument("--rationale", required=True)
    p.add_argument("--execute", action="store_true")

    p = commands.add_parser("publish-city", help="Publish one legalized production CITY")
    p.add_argument("--city-id", required=True, choices=CITY_IDS)
    p.add_argument("--submitted-by", required=True); p.add_argument("--approved-by", required=True)
    p.add_argument("--execute", action="store_true")

    p = commands.add_parser("status", help="Read-only Delivery-3 CITY authority/publication state")
    p.add_argument("--city-id", action="append", default=[])
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    output = args.output or None
    connection = connect_postgresql()
    try:
        if args.command == "qualify-city":
            mode = CandidateSourceMode.FROZEN_SOURCE_REUSE if args.candidate_source == "frozen" else CandidateSourceMode.SHARED_FACE_RECONSTRUCTION
            if mode is CandidateSourceMode.SHARED_FACE_RECONSTRUCTION and not args.fabric_run_id:
                raise SystemExit("--fabric-run-id is required for --candidate-source delivery2")
            receipt = PostgreSQLCityFeatureQualifier(connection).qualify(
                args.city_id,
                qualifier_actor_id=args.qualifier,
                candidate_source_mode=mode,
                fabric_run_id=args.fabric_run_id,
                precision_policy=_precision_policy(args),
                enforce_read_only_transaction=True,
            )
            write_json(_receipt_payload(receipt), output)
            return 0 if receipt.feature_qualified else 2
        if args.command == "status":
            selected = tuple(args.city_id) if args.city_id else CITY_IDS
            invalid = sorted(set(selected)-set(CITY_IDS))
            if invalid: raise SystemExit("unsupported CITY IDs: " + ",".join(invalid))
            with connection.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
            payload = _status(connection, selected)
            connection.rollback()
            write_json(payload, output); return 0
        if args.command == "adopt-city":
            _require_execute(args)
            technical = _load_receipt(args.qualification_receipt)
            repo = PostgreSQLAdministrativeAuthorityRepository(connection)
            receipt = GovernedAdministrativeAuthorityService(connection, repo).adopt_city(
                technical,
                effective_on=effective_date(args.effective_date),
                submitter_actor_id=args.submitter,
                approver_actor_id=args.approver,
                decision_reference=args.decision_reference,
                rationale=args.rationale,
            )
            write_json({"delivery":"P006.7.11.15.5-DELIVERY3-R1",**asdict(receipt),"authorityMutation":True}, output)
            return 0
        if args.command == "publish-city":
            _require_execute(args)
            receipt = PostgreSQLCityPublicationRepository(connection).publish_city(
                args.city_id, submitted_by=args.submitted_by, approved_by=args.approved_by
            )
            write_json({"delivery":"P006.7.11.15.5-DELIVERY3-R1",**asdict(receipt),"publicationMutation":True}, output)
            return 0
        raise SystemExit("unknown Delivery-3 command")
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
