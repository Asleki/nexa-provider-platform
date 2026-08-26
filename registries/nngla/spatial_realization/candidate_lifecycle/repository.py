"""Candidate-only persistence. No NG-GEO allocation, legalization or publication APIs exist here."""
from __future__ import annotations

from contextlib import contextmanager

from .contracts import CandidatePackage, CandidateQualificationDecision
from .fingerprints import canonical_json


class CandidateCollisionError(RuntimeError):
    pass


def _require_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise CandidateCollisionError(f"persisted {label} readback mismatch")


class MemoryCandidateLifecycleRepository:
    def __init__(self) -> None:
        self._packages: dict[str, CandidatePackage] = {}
        self._qualifications: dict[str, CandidateQualificationDecision] = {}

    def persist(self, package: CandidatePackage) -> CandidatePackage:
        current = self._packages.get(package.fabric_run_id)
        if current is not None:
            if current.package_sha256 != package.package_sha256:
                raise CandidateCollisionError("fabric run identity collision with different package digest")
            return current
        self._packages[package.fabric_run_id] = package
        return package

    def get(self, fabric_run_id: str) -> CandidatePackage | None:
        return self._packages.get(fabric_run_id)

    def persist_qualification(self, decision: CandidateQualificationDecision) -> CandidateQualificationDecision:
        current = self._qualifications.get(decision.qualification_id)
        if current is not None and current.decision_sha256 != decision.decision_sha256:
            raise CandidateCollisionError("qualification identity collision")
        self._qualifications.setdefault(decision.qualification_id, decision)
        return self._qualifications[decision.qualification_id]


class PostgreSQLCandidateLifecycleRepository:
    """Persists only to Delivery-2 candidate tables; never to canonical geometry authority."""
    def __init__(self, connection) -> None:
        self.connection = connection

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    @staticmethod
    def _root_readback(cur, package: CandidatePackage) -> None:
        cur.execute(
            "SELECT package_sha256,package_json FROM geography.nngla_shared_face_fabric_run WHERE fabric_run_id=%s",
            (package.fabric_run_id,),
        )
        row = cur.fetchone()
        if row is None or str(row[0]) != package.package_sha256:
            raise CandidateCollisionError("persisted fabric run digest mismatch")
        _require_equal("fabric run package JSON", canonical_json(row[1]), canonical_json(package))

    @staticmethod
    def _geometry_matches(cur, table: str, id_column: str, run_id: str, object_id: str, wkb_hex: str) -> bool:
        cur.execute(
            f"SELECT ST_Equals(geometry,ST_GeomFromEWKB(decode(%s,'hex'))) FROM geography.{table} WHERE fabric_run_id=%s AND {id_column}=%s",
            (wkb_hex, run_id, object_id),
        )
        row = cur.fetchone()
        return row is not None and bool(row[0])

    def verify_readback(self, package: CandidatePackage) -> CandidatePackage:
        """Verify package JSON plus every normalized candidate row before reuse succeeds."""
        with self.connection.cursor() as cur:
            self._root_readback(cur, package)

            cur.execute(
                """SELECT input_role,subject_id,administrative_type_code,canonical_name,source_candidate_id,geometry_sha256,source_path_reference
                FROM geography.nngla_shared_face_fabric_input WHERE fabric_run_id=%s ORDER BY input_role,subject_id""",
                (package.fabric_run_id,),
            )
            actual = tuple(tuple(str(v) for v in row) for row in cur.fetchall())
            expected = tuple(sorted((
                str(item["role"]), str(item["subjectId"]), str(item["administrativeType"]), str(item["canonicalName"]),
                str(item["sourceCandidateId"]), str(item["geometrySha256"]), str(item["sourcePathReference"]),
            ) for item in package.inputs))
            _require_equal("fabric input rows", actual, expected)

            cur.execute(
                "SELECT edge_id,geometry_sha256 FROM geography.nngla_shared_face_edge_candidate WHERE fabric_run_id=%s ORDER BY edge_id",
                (package.fabric_run_id,),
            )
            actual = tuple((str(row[0]), str(row[1])) for row in cur.fetchall())
            expected = tuple(sorted((str(item["edgeId"]), str(item["geometrySha256"])) for item in package.edges))
            _require_equal("edge candidate rows", actual, expected)
            for item in package.edges:
                if not self._geometry_matches(cur, "nngla_shared_face_edge_candidate", "edge_id", package.fabric_run_id, str(item["edgeId"]), str(item["geometryWkbHex"])):
                    raise CandidateCollisionError("persisted edge geometry readback mismatch")

            cur.execute(
                "SELECT edge_id,source_subject_id FROM geography.nngla_shared_face_edge_lineage WHERE fabric_run_id=%s ORDER BY edge_id,source_subject_id",
                (package.fabric_run_id,),
            )
            actual = tuple((str(row[0]), str(row[1])) for row in cur.fetchall())
            expected_set = {
                (str(edge["edgeId"]), str(lineage["subjectId"]))
                for edge in package.edges for lineage in edge["lineage"]
            }
            _require_equal("edge lineage rows", actual, tuple(sorted(expected_set)))

            cur.execute(
                "SELECT face_id,geometry_sha256,classification FROM geography.nngla_shared_face_face_candidate WHERE fabric_run_id=%s ORDER BY face_id",
                (package.fabric_run_id,),
            )
            actual = tuple((str(row[0]), str(row[1]), str(row[2])) for row in cur.fetchall())
            expected = tuple(sorted((str(item["faceId"]), str(item["geometrySha256"]), str(item["classification"])) for item in package.faces))
            _require_equal("face candidate rows", actual, expected)
            for item in package.faces:
                if not self._geometry_matches(cur, "nngla_shared_face_face_candidate", "face_id", package.fabric_run_id, str(item["faceId"]), str(item["geometryWkbHex"])):
                    raise CandidateCollisionError("persisted face geometry readback mismatch")

            cur.execute(
                """SELECT defect_id,defect_kind,geometry_sha256,residual_class,requires_governed_review
                FROM geography.nngla_shared_face_finding WHERE fabric_run_id=%s ORDER BY defect_id""",
                (package.fabric_run_id,),
            )
            actual = tuple((str(r[0]), str(r[1]), str(r[2]), str(r[3]), bool(r[4])) for r in cur.fetchall())
            expected = tuple(sorted((str(i["defectId"]), str(i["kind"]), str(i["geometrySha256"]), str(i["residualClass"]), bool(i["requiresGovernedReview"])) for i in package.defects))
            _require_equal("finding rows", actual, expected)
            for item in package.defects:
                if not self._geometry_matches(cur, "nngla_shared_face_finding", "defect_id", package.fabric_run_id, str(item["defectId"]), str(item["geometryWkbHex"])):
                    raise CandidateCollisionError("persisted finding geometry readback mismatch")

            cur.execute(
                """SELECT decision_id,decision_type,target_id,target_geometry_sha256,owner_subject_id,decision_kind,decision_reference,rationale,reviewer_actor_id,approver_actor_id,runtime_mode
                FROM geography.nngla_shared_face_governance_decision WHERE fabric_run_id=%s ORDER BY decision_id""",
                (package.fabric_run_id,),
            )
            actual = tuple((str(r[0]),str(r[1]),str(r[2]),str(r[3]),str(r[4] or ""),str(r[5]),str(r[6]),str(r[7]),str(r[8]),str(r[9]),str(r[10])) for r in cur.fetchall())
            expected = tuple(sorted((d.decision_id,d.decision_type,d.target_id,d.target_geometry_sha256,d.owner_subject_id,d.decision_kind,d.decision_reference,d.rationale,d.reviewer_actor_id,d.approver_actor_id,d.runtime_mode.value) for d in package.decisions))
            _require_equal("governance decision rows", actual, expected)

            cur.execute(
                """SELECT face_id,owner_subject_id,geometry_sha256,decision_kind,decision_reference
                FROM geography.nngla_shared_face_face_assignment WHERE fabric_run_id=%s ORDER BY face_id""",
                (package.fabric_run_id,),
            )
            actual = tuple(tuple(str(v) for v in row) for row in cur.fetchall())
            expected = tuple(sorted((str(i["faceId"]),str(i["ownerSubjectId"]),str(i["geometrySha256"]),str(i["decisionKind"]),str(i["decisionReference"])) for i in package.assignments))
            _require_equal("face assignment rows", actual, expected)

            cur.execute(
                "SELECT candidate_id,subject_id,geometry_sha256 FROM geography.nngla_shared_face_geometry_candidate WHERE fabric_run_id=%s ORDER BY candidate_id",
                (package.fabric_run_id,),
            )
            actual = tuple((str(r[0]),str(r[1]),str(r[2])) for r in cur.fetchall())
            expected = tuple(sorted((str(i["candidateId"]),str(i["subjectId"]),str(i["geometrySha256"])) for i in package.sibling_candidates))
            _require_equal("geometry candidate rows", actual, expected)
            for item in package.sibling_candidates:
                if not self._geometry_matches(cur, "nngla_shared_face_geometry_candidate", "candidate_id", package.fabric_run_id, str(item["candidateId"]), str(item["geometryWkbHex"])):
                    raise CandidateCollisionError("persisted candidate geometry readback mismatch")
        return package

    def persist(self, package: CandidatePackage) -> CandidatePackage:
        payload = canonical_json(package)
        with self.connection.cursor() as cur:
            cur.execute(
                """INSERT INTO geography.nngla_shared_face_fabric_run
                (fabric_run_id,requested_root_place_id,parent_administrative_area_id,fabric_level,runtime_mode,
                 scope_fingerprint,input_digest,runtime_signature_digest,edge_graph_sha256,face_set_sha256,
                 assignment_sha256,qualification_sha256,author_actor_id,lifecycle_status,parent_candidate_id,
                 parent_candidate_geometry_sha256,package_sha256,package_json)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULLIF(%s,''),NULLIF(%s,''),%s,%s,NULLIF(%s,''),NULLIF(%s,''),%s,%s::jsonb)
                ON CONFLICT (fabric_run_id) DO NOTHING""",
                (package.fabric_run_id, package.requested_root_place_id, package.parent_administrative_area_id,
                 package.fabric_level, package.runtime_mode.value, package.scope_fingerprint, package.input_digest,
                 package.runtime_signature_digest, package.edge_graph_sha256, package.face_set_sha256,
                 package.assignment_sha256, package.qualification_sha256, package.author_actor_id,
                 package.lifecycle_status.value, package.parent_candidate_id, package.parent_candidate_geometry_sha256,
                 package.package_sha256, payload),
            )
            self._root_readback(cur, package)

            for item in package.inputs:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_fabric_input
                    (fabric_run_id,input_role,subject_id,administrative_type_code,canonical_name,source_candidate_id,geometry_sha256,source_path_reference)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,item["role"],item["subjectId"],item["administrativeType"],item["canonicalName"],item["sourceCandidateId"],item["geometrySha256"],item["sourcePathReference"]),
                )
            for edge in package.edges:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_edge_candidate
                    (fabric_run_id,edge_id,geometry_sha256,geometry) VALUES(%s,%s,%s,ST_GeomFromEWKB(decode(%s,'hex'))) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,edge["edgeId"],edge["geometrySha256"],edge["geometryWkbHex"]),
                )
                for lineage in edge["lineage"]:
                    cur.execute(
                        """INSERT INTO geography.nngla_shared_face_edge_lineage(fabric_run_id,edge_id,source_subject_id)
                        VALUES(%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (package.fabric_run_id,edge["edgeId"],lineage["subjectId"]),
                    )
            for face in package.faces:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_face_candidate
                    (fabric_run_id,face_id,geometry_sha256,classification,geometry)
                    VALUES(%s,%s,%s,%s,ST_GeomFromEWKB(decode(%s,'hex'))) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,face["faceId"],face["geometrySha256"],face["classification"],face["geometryWkbHex"]),
                )
            for defect in package.defects:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_finding
                    (fabric_run_id,defect_id,defect_kind,geometry_sha256,residual_class,requires_governed_review,geometry)
                    VALUES(%s,%s,%s,%s,%s,%s,ST_GeomFromEWKB(decode(%s,'hex'))) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,defect["defectId"],defect["kind"],defect["geometrySha256"],defect["residualClass"],defect["requiresGovernedReview"],defect["geometryWkbHex"]),
                )
            for decision in package.decisions:
                if decision.fabric_run_id != package.fabric_run_id or decision.scope_fingerprint != package.scope_fingerprint:
                    raise CandidateCollisionError("governance decision package binding mismatch")
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_governance_decision
                    (decision_id,fabric_run_id,decision_type,target_id,target_geometry_sha256,owner_subject_id,decision_kind,decision_reference,rationale,reviewer_actor_id,approver_actor_id,runtime_mode)
                    VALUES(%s,%s,%s,%s,%s,NULLIF(%s,''),%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (decision.decision_id,decision.fabric_run_id,decision.decision_type,decision.target_id,decision.target_geometry_sha256,decision.owner_subject_id,decision.decision_kind,decision.decision_reference,decision.rationale,decision.reviewer_actor_id,decision.approver_actor_id,decision.runtime_mode.value),
                )
            for item in package.assignments:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_face_assignment
                    (fabric_run_id,face_id,owner_subject_id,geometry_sha256,decision_kind,decision_reference)
                    VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,item["faceId"],item["ownerSubjectId"],item["geometrySha256"],item["decisionKind"],item["decisionReference"]),
                )
            for item in package.sibling_candidates:
                cur.execute(
                    """INSERT INTO geography.nngla_shared_face_geometry_candidate
                    (fabric_run_id,candidate_id,subject_id,geometry_sha256,geometry)
                    VALUES(%s,%s,%s,%s,ST_GeomFromEWKB(decode(%s,'hex'))) ON CONFLICT DO NOTHING""",
                    (package.fabric_run_id,item["candidateId"],item["subjectId"],item["geometrySha256"],item["geometryWkbHex"]),
                )
        return self.verify_readback(package)

    def persist_qualification(self, decision: CandidateQualificationDecision) -> CandidateQualificationDecision:
        with self.connection.cursor() as cur:
            cur.execute(
                """INSERT INTO geography.nngla_shared_face_qualification_decision
                (qualification_id,fabric_run_id,package_sha256,qualifier_actor_id,status,valid_all,every_child_covered_by_parent,
                 union_covered_by_parent,parent_covered_by_union,symmetric_difference_m2,positive_overlap_m2,decision_sha256)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (decision.qualification_id,decision.fabric_run_id,decision.package_sha256,decision.qualifier_actor_id,
                 decision.status.value,decision.valid_all,decision.every_child_covered_by_parent,decision.union_covered_by_parent,
                 decision.parent_covered_by_union,decision.symmetric_difference_m2,decision.positive_overlap_m2,decision.decision_sha256),
            )
            cur.execute("SELECT decision_sha256 FROM geography.nngla_shared_face_qualification_decision WHERE qualification_id=%s",(decision.qualification_id,))
            row=cur.fetchone()
        if row is None or str(row[0]) != decision.decision_sha256:
            raise CandidateCollisionError("persisted qualification digest mismatch")
        return decision

    def raw_package_json(self, fabric_run_id: str) -> dict | None:
        with self.connection.cursor() as cur:
            cur.execute("SELECT package_json FROM geography.nngla_shared_face_fabric_run WHERE fabric_run_id=%s", (fabric_run_id,))
            row = cur.fetchone()
        return None if row is None else dict(row[0])


__all__ = ["CandidateCollisionError", "MemoryCandidateLifecycleRepository", "PostgreSQLCandidateLifecycleRepository"]
