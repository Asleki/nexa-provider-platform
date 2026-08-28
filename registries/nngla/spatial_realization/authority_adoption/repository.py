"""Transactional PostgreSQL writer for one qualified CITY authority adoption."""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256

from .contracts import (
    CityAuthorityAdoptionRequest,
    CityAuthorityReceipt,
    CityQualificationReceipt,
    PrecisionMode,
    PrecisionPolicy,
    stable_digest,
    stable_id,
)


class AuthorityWriteError(RuntimeError):
    pass


def _sha_wkb_hex(value: str) -> str:
    return sha256(bytes.fromhex(value)).hexdigest()


class PostgreSQLAdministrativeAuthorityRepository:
    """Adopt one CITY only after exact qualification is re-verified.

    The repository never accepts arbitrary GeoJSON from a CLI. The service
    resolves the candidate through the frozen-source or Delivery-2 adapters,
    re-runs the qualifier, and passes the exact raw WKB plus the bound receipt.
    """

    def __init__(self, connection) -> None:
        self.connection = connection

    @contextmanager
    def transaction(self):
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _persist_qualification(self, cur, q: CityQualificationReceipt) -> None:
        if not q.feature_qualified:
            raise AuthorityWriteError("only CITY_READY_FOR_AUTHORITY may become durable qualification")
        cur.execute(
            """INSERT INTO geography.nngla_city_feature_qualification(
                   qualification_id,city_administrative_area_id,root_place_id,candidate_source_mode,candidate_id,
                   raw_candidate_geometry_sha256,evaluated_candidate_geometry_sha256,source_geometry_sha256,
                   source_dataset_id,source_dataset_version,source_path_reference,fabric_run_id,package_sha256,
                   validation_parent_id,parent_evidence_kind,parent_evidence_id,raw_parent_geometry_sha256,
                   evaluated_parent_geometry_sha256,parent_qualification_reference,parent_source_path_reference,
                   peer_evidence_digest,precision_policy_id,precision_policy_sha256,precision_mode,
                   precision_grid_size_degrees,precision_evidence_reference,valid_geometry,polygonal,non_empty,
                   srid_correct,parent_evidence_valid,city_covered_by_parent,raw_area_outside_parent_m2,
                   area_outside_parent_m2,raw_positive_city_peer_overlap_m2,positive_city_peer_overlap_m2,
                   raw_positive_municipality_overlap_m2,positive_municipality_overlap_m2,reference_point_covered,
                   unresolved_city_affecting_defect_count,numerical_residue,source_provenance_bound,qualifier_actor_id,
                   runtime_mode,feature_qualification_status,qualification_sha256)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'production','FEATURE_QUALIFIED',%s)
               ON CONFLICT (qualification_id) DO NOTHING""",
            (
                q.qualification_id,q.city_administrative_area_id,q.root_place_id,q.candidate_source_mode.value,q.candidate_id,
                q.raw_candidate_geometry_sha256,q.evaluated_candidate_geometry_sha256,q.source_geometry_sha256,
                q.source_dataset_id,q.source_dataset_version,q.source_path_reference,q.fabric_run_id or None,q.package_sha256 or None,
                q.validation_parent_id,q.parent_evidence_kind,q.parent_evidence_id,q.raw_parent_geometry_sha256,
                q.evaluated_parent_geometry_sha256,q.parent_qualification_reference,q.parent_source_path_reference,
                q.peer_evidence_digest,q.precision_policy_id,q.precision_policy_sha256,q.precision_mode.value,
                q.precision_grid_size_degrees,q.precision_evidence_reference,q.valid_geometry,q.polygonal,q.non_empty,
                q.srid_correct,q.parent_evidence_valid,q.city_covered_by_parent,q.raw_area_outside_parent_m2,
                q.area_outside_parent_m2,q.raw_positive_city_peer_overlap_m2,q.positive_city_peer_overlap_m2,
                q.raw_positive_municipality_overlap_m2,q.positive_municipality_overlap_m2,q.reference_point_covered,
                q.unresolved_city_affecting_defect_count,q.numerical_residue,q.source_provenance_bound,q.qualifier_actor_id,
                q.qualification_sha256,
            ),
        )
        cur.execute(
            "SELECT qualification_sha256 FROM geography.nngla_city_feature_qualification WHERE qualification_id=%s FOR SHARE",
            (q.qualification_id,),
        )
        row = cur.fetchone()
        if row is None or str(row[0]) != q.qualification_sha256:
            raise AuthorityWriteError("durable CITY qualification readback mismatch")

    def adopt_city(
        self,
        qualification: CityQualificationReceipt,
        request: CityAuthorityAdoptionRequest,
        *,
        raw_candidate_wkb_hex: str,
        precision_policy: PrecisionPolicy,
    ) -> CityAuthorityReceipt:
        if not qualification.feature_qualified:
            raise AuthorityWriteError("CITY is not ready for authority")
        if qualification.runtime_mode != "production":
            raise AuthorityWriteError("CITY authority adoption requires production qualification")
        if request.qualification_id != qualification.qualification_id or request.qualification_sha256 != qualification.qualification_sha256:
            raise AuthorityWriteError("adoption request qualification binding mismatch")
        if request.city_administrative_area_id != qualification.city_administrative_area_id:
            raise AuthorityWriteError("adoption request CITY differs from qualification")
        if request.candidate_id != qualification.candidate_id or request.candidate_geometry_sha256 != qualification.evaluated_candidate_geometry_sha256:
            raise AuthorityWriteError("adoption request candidate binding mismatch")
        if request.validation_parent_id != qualification.validation_parent_id or request.parent_evidence_id != qualification.parent_evidence_id:
            raise AuthorityWriteError("adoption request parent evidence identity mismatch")
        if request.parent_geometry_sha256 != qualification.evaluated_parent_geometry_sha256:
            raise AuthorityWriteError("adoption request parent geometry hash mismatch")
        if request.peer_evidence_digest != qualification.peer_evidence_digest:
            raise AuthorityWriteError("adoption request peer evidence mismatch")
        if request.precision_policy_sha256 != qualification.precision_policy_sha256 or precision_policy.policy_sha256 != qualification.precision_policy_sha256:
            raise AuthorityWriteError("adoption request precision policy mismatch")

        with self.transaction():
            with self.connection.cursor() as cur:
                self._persist_qualification(cur, qualification)

                cur.execute(
                    """SELECT administrative_type_code,geometry_reference
                       FROM geography.nngla_administrative_area
                       WHERE administrative_area_id=%s FOR UPDATE""",
                    (qualification.city_administrative_area_id,),
                )
                admin = cur.fetchone()
                if admin is None or str(admin[0]) != "CITY":
                    raise AuthorityWriteError("Delivery 3 authority adoption accepts CITY administrative areas only")
                predecessor_geometry_id = str(admin[1]) if admin[1] not in (None, "") else None

                cur.execute(
                    """INSERT INTO geography.nngla_administrative_geometry_adoption_decision(
                           adoption_decision_id,administrative_area_id,qualification_id,qualification_sha256,
                           candidate_source_mode,candidate_id,candidate_geometry_sha256,validation_parent_id,
                           parent_evidence_id,parent_geometry_sha256,parent_qualification_reference,peer_evidence_digest,
                           precision_policy_id,precision_policy_sha256,effective_on,qualifier_actor_id,submitter_actor_id,
                           approver_actor_id,decision_reference,rationale,decision_status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'APPROVED')
                       ON CONFLICT (adoption_decision_id) DO NOTHING""",
                    (
                        request.decision_id,request.city_administrative_area_id,request.qualification_id,request.qualification_sha256,
                        request.candidate_source_mode.value,request.candidate_id,request.candidate_geometry_sha256,
                        request.validation_parent_id,request.parent_evidence_id,request.parent_geometry_sha256,
                        request.parent_qualification_reference,request.peer_evidence_digest,request.precision_policy_id,
                        request.precision_policy_sha256,request.effective_on,request.qualifier_actor_id,request.submitter_actor_id,
                        request.approver_actor_id,request.decision_reference,request.rationale,
                    ),
                )

                reservation_id = stable_id("geometry-reservation:nngla:d3:", {
                    "decision": request.decision_id, "city": request.city_administrative_area_id,
                })
                idempotency_key = stable_digest({
                    "decision": request.decision_id,
                    "qualification": qualification.qualification_sha256,
                    "candidate": qualification.candidate_id,
                })
                cur.execute(
                    "SELECT geography.nngla_reserve_geometry_id(%s,%s,%s,'ADMINISTRATIVE_BOUNDARY')",
                    (reservation_id,idempotency_key,request.city_administrative_area_id),
                )
                reserved = cur.fetchone()
                if reserved is None or not str(reserved[0]).startswith("NG-GEO-"):
                    raise AuthorityWriteError("governed NG-GEO reservation failed")
                geometry_id = str(reserved[0])

                grid = precision_policy.normalization_grid
                cur.execute(
                    """INSERT INTO geography.nngla_geometry_version(
                           geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,
                           geometry,valid_from,valid_to,supersedes_geometry_id,source_sha256)
                       SELECT %s,%s,'production','ADMINISTRATIVE_BOUNDARY','NG-CRS-EPSG4326',
                              CASE GeometryType(g) WHEN 'POLYGON' THEN 'POLYGON' ELSE 'MULTIPOLYGON' END,
                              g,%s,NULL,%s,%s
                       FROM (
                         SELECT CASE WHEN %s::double precision IS NULL
                                     THEN ST_GeomFromEWKB(decode(%s,'hex'))
                                     ELSE ST_ReducePrecision(ST_GeomFromEWKB(decode(%s,'hex')),%s)
                                END AS g
                       ) q
                       ON CONFLICT (geometry_id) DO NOTHING""",
                    (
                        geometry_id,request.city_administrative_area_id,request.effective_on,predecessor_geometry_id,
                        qualification.evaluated_candidate_geometry_sha256,
                        grid,raw_candidate_wkb_hex,raw_candidate_wkb_hex,grid,
                    ),
                )
                cur.execute("SELECT encode(ST_AsEWKB(geometry),'hex') FROM geography.nngla_geometry_version WHERE geometry_id=%s", (geometry_id,))
                readback = cur.fetchone()
                if readback is None or _sha_wkb_hex(str(readback[0])) != qualification.evaluated_candidate_geometry_sha256:
                    raise AuthorityWriteError("qualified CITY geometry readback hash mismatch")

                if predecessor_geometry_id:
                    cur.execute(
                        """UPDATE geography.nngla_administrative_geometry_assignment
                           SET effective_to=%s,assignment_status='SUPERSEDED'
                           WHERE administrative_area_id=%s AND effective_to IS NULL AND assignment_status='EFFECTIVE'""",
                        (request.effective_on,request.city_administrative_area_id),
                    )
                    cur.execute(
                        "UPDATE geography.nngla_geometry_version SET valid_to=%s WHERE geometry_id=%s AND valid_to IS NULL",
                        (request.effective_on,predecessor_geometry_id),
                    )
                    cur.execute(
                        """UPDATE geography.nngla_geometry_authority_record
                           SET valid_to=%s,superseded_by_geometry_id=%s
                           WHERE geometry_id=%s AND valid_to IS NULL""",
                        (request.effective_on,geometry_id,predecessor_geometry_id),
                    )

                cur.execute(
                    """INSERT INTO geography.nngla_geometry_authority_record(
                           geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,
                           source_version,geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,
                           valid_from,valid_to,supersedes_geometry_id,superseded_by_geometry_id,qualification_status,
                           publication_status,checksum_sha256,source_path_reference,runtime_effect_scope)
                       SELECT g.geometry_id,'ADMINISTRATIVE_AREA',g.subject_id,'ADMINISTRATIVE_BOUNDARY',%s,%s,%s,
                              g.geometry_type_code,'NG-CRS-EPSG4326','QUALIFIED_LEGAL_ADMINISTRATIVE_BOUNDARY',
                              ST_NPoints(g.geometry),ST_NumGeometries(g.geometry),%s,NULL,%s,NULL,'QUALIFIED','NOT_PUBLISHED',
                              %s,%s,'PRODUCTION_ONLY'
                       FROM geography.nngla_geometry_version g WHERE g.geometry_id=%s
                       ON CONFLICT (geometry_id) DO NOTHING""",
                    (
                        qualification.candidate_id,qualification.source_dataset_id,qualification.source_dataset_version,
                        request.effective_on,predecessor_geometry_id,qualification.evaluated_candidate_geometry_sha256,
                        qualification.source_path_reference,geometry_id,
                    ),
                )

                assignment_id = stable_id("admin-geometry-assignment:nngla:", {
                    "city":request.city_administrative_area_id,"geometry":geometry_id,"qualification":request.qualification_id,
                    "parentEvidence":request.parent_evidence_id,"effective":request.effective_on,
                })
                assignment_sha = stable_digest({
                    "assignmentId":assignment_id,"city":request.city_administrative_area_id,"geometry":geometry_id,
                    "candidate":request.candidate_id,"qualification":request.qualification_id,"adoption":request.decision_id,
                    "parent":request.validation_parent_id,"parentEvidence":request.parent_evidence_id,
                    "parentGeometrySha256":request.parent_geometry_sha256,"effectiveFrom":request.effective_on,
                })
                cur.execute(
                    """INSERT INTO geography.nngla_administrative_geometry_assignment(
                           assignment_id,administrative_area_id,geometry_id,candidate_id,qualification_id,adoption_decision_id,
                           validation_parent_id,parent_evidence_id,parent_geometry_sha256,effective_from,effective_to,
                           assignment_status,assignment_sha256)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,'EFFECTIVE',%s)
                       ON CONFLICT (assignment_id) DO NOTHING""",
                    (
                        assignment_id,request.city_administrative_area_id,geometry_id,request.candidate_id,request.qualification_id,
                        request.decision_id,request.validation_parent_id,request.parent_evidence_id,request.parent_geometry_sha256,
                        request.effective_on,assignment_sha,
                    ),
                )

                legalization_id = stable_id("admin-legalization:nngla:", {
                    "city":request.city_administrative_area_id,"geometry":geometry_id,"assignment":assignment_id,
                })
                legalization_sha = stable_digest({
                    "legalizationId":legalization_id,"city":request.city_administrative_area_id,"geometry":geometry_id,
                    "geometrySha256":qualification.evaluated_candidate_geometry_sha256,"candidate":request.candidate_id,
                    "qualification":request.qualification_id,"assignment":assignment_id,"effectiveOn":request.effective_on,
                    "submitter":request.submitter_actor_id,"approver":request.approver_actor_id,
                    "decisionReference":request.decision_reference,
                })
                cur.execute(
                    """INSERT INTO geography.nngla_administrative_legalization_decision(
                           legalization_id,administrative_area_id,geometry_id,geometry_sha256,candidate_id,qualification_id,
                           assignment_id,effective_on,submitter_actor_id,approver_actor_id,decision_reference,decision_status,
                           decision_sha256)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'LEGALIZED',%s)
                       ON CONFLICT (legalization_id) DO NOTHING""",
                    (
                        legalization_id,request.city_administrative_area_id,geometry_id,
                        qualification.evaluated_candidate_geometry_sha256,request.candidate_id,request.qualification_id,
                        assignment_id,request.effective_on,request.submitter_actor_id,request.approver_actor_id,
                        request.decision_reference,legalization_sha,
                    ),
                )

                cur.execute(
                    """UPDATE geography.nngla_administrative_area
                       SET geometry_reference=%s,boundary_status='LEGALIZED',lifecycle_status_code='ACTIVE',candidate_status='LEGALIZED'
                       WHERE administrative_area_id=%s""",
                    (geometry_id,request.city_administrative_area_id),
                )
                if getattr(cur,"rowcount",1) != 1:
                    raise AuthorityWriteError("CITY current geometry pointer update failed")

                transaction_sha = stable_digest({
                    "decision":request.decision_id,"qualification":request.qualification_sha256,"geometry":geometry_id,
                    "assignment":assignment_id,"legalization":legalization_id,
                })
                receipt_id = stable_id("city-authority-receipt:nngla:", transaction_sha)
                cur.execute(
                    """INSERT INTO geography.nngla_city_authority_receipt(
                           receipt_id,administrative_area_id,geometry_id,qualification_id,adoption_decision_id,
                           assignment_id,legalization_id,transaction_sha256,runtime_mode,status)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'production','APPLIED')
                       ON CONFLICT (receipt_id) DO NOTHING""",
                    (
                        receipt_id,request.city_administrative_area_id,geometry_id,request.qualification_id,
                        request.decision_id,assignment_id,legalization_id,transaction_sha,
                    ),
                )

                cur.execute(
                    """SELECT a.geometry_reference,ass.assignment_status,l.decision_status,ar.qualification_status,
                              q.qualification_sha256
                       FROM geography.nngla_administrative_area a
                       JOIN geography.nngla_administrative_geometry_assignment ass
                         ON ass.administrative_area_id=a.administrative_area_id AND ass.geometry_id=a.geometry_reference
                        AND ass.assignment_status='EFFECTIVE' AND ass.effective_to IS NULL
                       JOIN geography.nngla_administrative_legalization_decision l
                         ON l.assignment_id=ass.assignment_id AND l.decision_status='LEGALIZED'
                       JOIN geography.nngla_geometry_authority_record ar
                         ON ar.geometry_id=a.geometry_reference AND ar.qualification_status='QUALIFIED' AND ar.valid_to IS NULL
                       JOIN geography.nngla_city_feature_qualification q ON q.qualification_id=ass.qualification_id
                       WHERE a.administrative_area_id=%s""",
                    (request.city_administrative_area_id,),
                )
                rb = cur.fetchone()
                if rb is None or str(rb[0]) != geometry_id or str(rb[1]) != "EFFECTIVE" or str(rb[2]) != "LEGALIZED" or str(rb[3]) != "QUALIFIED" or str(rb[4]) != qualification.qualification_sha256:
                    raise AuthorityWriteError("CITY authority chain readback mismatch")

        return CityAuthorityReceipt(
            decision_id=request.decision_id,
            city_administrative_area_id=request.city_administrative_area_id,
            geometry_id=geometry_id,
            assignment_id=assignment_id,
            legalization_id=legalization_id,
            qualification_id=request.qualification_id,
            transaction_sha256=transaction_sha,
        )


__all__ = ["AuthorityWriteError", "PostgreSQLAdministrativeAuthorityRepository"]
