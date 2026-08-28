"""Reusable SELECT-only PostGIS CITY feature qualifier for Delivery 3 R1."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from registries.nngla.spatial_realization.source import (
    administrative_children,
    administrative_reference_seed,
    administrative_row,
    city_roots,
    geometry_for_admin,
)

from .contracts import (
    CandidateSourceMode,
    CityCandidateEvidence,
    CityQualificationReceipt,
    CityQualificationStatus,
    GeometryEvidence,
    PrecisionMode,
    PrecisionPolicy,
    SOURCE_EXACT_PRECISION,
    stable_digest,
    stable_id,
)
from .precision_normalization import numerical_residue


class CityQualificationError(RuntimeError):
    pass


def _sha_wkb_hex(value: str) -> str:
    return sha256(bytes.fromhex(value)).hexdigest()


def _city_root_for_admin(administrative_area_id: str):
    for root in city_roots():
        if root.administrative_area_id == administrative_area_id:
            return root
    raise CityQualificationError(f"unsupported CITY administrative area: {administrative_area_id}")


@dataclass(frozen=True, slots=True)
class _PairEvaluation:
    polygonal: bool
    non_empty: bool
    valid_geometry: bool
    srid_correct: bool
    parent_evidence_valid: bool
    city_covered_by_parent: bool
    raw_area_outside_parent_m2: float
    area_outside_parent_m2: float
    reference_point_covered: bool
    raw_candidate_wkb_hex: str
    evaluated_candidate_wkb_hex: str
    raw_parent_wkb_hex: str
    evaluated_parent_wkb_hex: str


class PostgreSQLCityEvidenceResolver:
    """Resolve exact CITY/parent/peer evidence without making it authoritative."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def _wkb_from_geojson(self, payload: str) -> str:
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT encode(ST_AsEWKB(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)),'hex')",
                (payload,),
            )
            row = cur.fetchone()
        if row is None or not row[0]:
            raise CityQualificationError("PostGIS could not materialize frozen geometry evidence")
        return str(row[0])

    def frozen_candidate(self, city_administrative_area_id: str) -> CityCandidateEvidence:
        root = _city_root_for_admin(city_administrative_area_id)
        candidate = geometry_for_admin(city_administrative_area_id, root.place_id)
        return CityCandidateEvidence(
            city_administrative_area_id=city_administrative_area_id,
            root_place_id=root.place_id,
            candidate_source_mode=CandidateSourceMode.FROZEN_SOURCE_REUSE,
            candidate_id=candidate.source_candidate_id,
            candidate_geometry_sha256=candidate.checksum_sha256,
            source_geometry_sha256=candidate.checksum_sha256,
            source_dataset_id=candidate.source_dataset_id,
            source_dataset_version=candidate.source_dataset_version,
            source_path_reference=candidate.source_path_reference,
            runtime_mode="production",
            geometry_wkb_hex=self._wkb_from_geojson(candidate.payload),
        )

    def delivery2_candidate(self, city_administrative_area_id: str, fabric_run_id: str) -> CityCandidateEvidence:
        root = _city_root_for_admin(city_administrative_area_id)
        with self.connection.cursor() as cur:
            cur.execute(
                """SELECT c.candidate_id,c.geometry_sha256,encode(ST_AsEWKB(c.geometry),'hex'),
                          r.package_sha256,r.runtime_mode,
                          i.geometry_sha256,i.source_path_reference
                   FROM geography.nngla_shared_face_geometry_candidate c
                   JOIN geography.nngla_shared_face_fabric_run r ON r.fabric_run_id=c.fabric_run_id
                   JOIN geography.nngla_shared_face_fabric_input i
                     ON i.fabric_run_id=c.fabric_run_id AND i.subject_id=c.subject_id
                   WHERE c.fabric_run_id=%s AND c.subject_id=%s
                   ORDER BY c.candidate_id LIMIT 1""",
                (fabric_run_id, city_administrative_area_id),
            )
            row = cur.fetchone()
        if row is None:
            raise CityQualificationError("Delivery-2 CITY candidate was not found")
        if str(row[4]) != "production":
            raise CityQualificationError("simulation Delivery-2 candidate cannot qualify production CITY authority")
        source = geometry_for_admin(city_administrative_area_id, root.place_id)
        if str(row[6]) != source.source_path_reference:
            raise CityQualificationError("Delivery-2 CITY candidate source path no longer matches locked evidence")
        return CityCandidateEvidence(
            city_administrative_area_id=city_administrative_area_id,
            root_place_id=root.place_id,
            candidate_source_mode=CandidateSourceMode.SHARED_FACE_RECONSTRUCTION,
            candidate_id=str(row[0]),
            candidate_geometry_sha256=str(row[1]),
            source_geometry_sha256=str(row[5]),
            source_dataset_id=source.source_dataset_id,
            source_dataset_version=source.source_dataset_version,
            source_path_reference=str(row[6]),
            runtime_mode="production",
            geometry_wkb_hex=str(row[2]),
            fabric_run_id=fabric_run_id,
            package_sha256=str(row[3]),
        )

    def validation_evidence(self, administrative_area_id: str, root_place_id: str) -> GeometryEvidence:
        """Prefer current qualified production authority, then locked Bundle-19B evidence."""
        with self.connection.cursor() as cur:
            cur.execute(
                """SELECT a.administrative_type_code,a.canonical_name,g.geometry_id,
                          encode(ST_AsEWKB(g.geometry),'hex'),ar.checksum_sha256,
                          ar.source_dataset_id,ar.source_version,ar.source_path_reference
                   FROM geography.nngla_administrative_area a
                   JOIN geography.nngla_geometry_version g
                     ON g.subject_id=a.administrative_area_id AND g.runtime_mode='production' AND g.valid_to IS NULL
                   JOIN geography.nngla_geometry_authority_record ar
                     ON ar.geometry_id=g.geometry_id AND ar.subject_id=a.administrative_area_id
                    AND ar.qualification_status='QUALIFIED' AND ar.valid_to IS NULL
                   WHERE a.administrative_area_id=%s
                   ORDER BY g.created_at DESC,g.geometry_id DESC LIMIT 1""",
                (administrative_area_id,),
            )
            row = cur.fetchone()
        if row is not None:
            wkb_hex = str(row[3])
            return GeometryEvidence(
                subject_id=administrative_area_id,
                administrative_type_code=str(row[0]),
                canonical_name=str(row[1]),
                evidence_kind="CURRENT_QUALIFIED_AUTHORITY",
                evidence_id=str(row[2]),
                geometry_sha256=_sha_wkb_hex(wkb_hex),
                source_geometry_sha256=str(row[4]),
                source_dataset_id=str(row[5]),
                source_dataset_version=str(row[6]),
                source_path_reference=str(row[7]),
                runtime_mode="production",
                qualification_reference=f"QUALIFIED_AUTHORITY:{row[2]}",
                geometry_wkb_hex=wkb_hex,
            )
        frozen = geometry_for_admin(administrative_area_id, root_place_id)
        row_meta = administrative_row(administrative_area_id)
        wkb_hex = self._wkb_from_geojson(frozen.payload)
        return GeometryEvidence(
            subject_id=administrative_area_id,
            administrative_type_code=row_meta.administrative_type_code,
            canonical_name=row_meta.canonical_name,
            evidence_kind="LOCKED_FROZEN_REFERENCE",
            evidence_id=frozen.source_candidate_id,
            geometry_sha256=_sha_wkb_hex(wkb_hex),
            source_geometry_sha256=frozen.checksum_sha256,
            source_dataset_id=frozen.source_dataset_id,
            source_dataset_version=frozen.source_dataset_version,
            source_path_reference=frozen.source_path_reference,
            runtime_mode="shared_reference",
            qualification_reference="BUNDLE19B_LOCKED_QUALIFIED_REFERENCE",
            geometry_wkb_hex=wkb_hex,
        )

    def peers(self, city_administrative_area_id: str, parent_id: str, root_place_id: str) -> tuple[GeometryEvidence, ...]:
        rows = []
        for item in administrative_children(parent_id):
            if item.administrative_area_id == city_administrative_area_id:
                continue
            rows.append(self.validation_evidence(item.administrative_area_id, root_place_id))
        return tuple(rows)


class PostgreSQLCityFeatureQualifier:
    """Evaluate one CITY using exact PostGIS predicates and no authority mutation."""

    def __init__(self, connection) -> None:
        self.connection = connection
        self.resolver = PostgreSQLCityEvidenceResolver(connection)

    def _evaluate_pair(
        self,
        candidate: CityCandidateEvidence,
        parent: GeometryEvidence,
        *, longitude: float,
        latitude: float,
        policy: PrecisionPolicy,
    ) -> _PairEvaluation:
        grid = policy.normalization_grid
        with self.connection.cursor() as cur:
            cur.execute(
                """WITH raw AS (
                       SELECT ST_GeomFromEWKB(decode(%s,'hex')) AS c,
                              ST_GeomFromEWKB(decode(%s,'hex')) AS p,
                              ST_SetSRID(ST_Point(%s,%s),4326) AS rp
                   ), eval AS (
                       SELECT c,p,rp,
                              CASE WHEN %s::double precision IS NULL THEN c ELSE ST_ReducePrecision(c,%s) END AS ec,
                              CASE WHEN %s::double precision IS NULL THEN p ELSE ST_ReducePrecision(p,%s) END AS ep,
                              CASE WHEN %s::double precision IS NULL THEN rp ELSE ST_ReducePrecision(rp,%s) END AS erp
                       FROM raw
                   )
                   SELECT GeometryType(c) IN ('POLYGON','MULTIPOLYGON'),NOT ST_IsEmpty(c),ST_IsValid(c),ST_SRID(c)=4326,
                          ST_IsValid(p) AND NOT ST_IsEmpty(p) AND ST_SRID(p)=4326,
                          ST_CoveredBy(ec,ep),
                          ST_Area(ST_Difference(c,p)::geography),
                          ST_Area(ST_Difference(ec,ep)::geography),
                          ST_Covers(ec,erp),
                          encode(ST_AsEWKB(c),'hex'),encode(ST_AsEWKB(ec),'hex'),
                          encode(ST_AsEWKB(p),'hex'),encode(ST_AsEWKB(ep),'hex')
                   FROM eval""",
                (
                    candidate.geometry_wkb_hex, parent.geometry_wkb_hex, float(longitude), float(latitude),
                    grid, grid, grid, grid, grid, grid,
                ),
            )
            row = cur.fetchone()
        if row is None:
            raise CityQualificationError("PostGIS CITY qualification returned no result")
        return _PairEvaluation(
            polygonal=bool(row[0]), non_empty=bool(row[1]), valid_geometry=bool(row[2]), srid_correct=bool(row[3]),
            parent_evidence_valid=bool(row[4]), city_covered_by_parent=bool(row[5]),
            raw_area_outside_parent_m2=float(row[6]), area_outside_parent_m2=float(row[7]),
            reference_point_covered=bool(row[8]), raw_candidate_wkb_hex=str(row[9]), evaluated_candidate_wkb_hex=str(row[10]),
            raw_parent_wkb_hex=str(row[11]), evaluated_parent_wkb_hex=str(row[12]),
        )

    def _peer_overlap(self, candidate_wkb_hex: str, peer_wkb_hex: str, policy: PrecisionPolicy) -> tuple[bool, float, float]:
        grid = policy.normalization_grid
        with self.connection.cursor() as cur:
            cur.execute(
                """WITH raw AS (
                       SELECT ST_GeomFromEWKB(decode(%s,'hex')) AS c,ST_GeomFromEWKB(decode(%s,'hex')) AS p
                   ), eval AS (
                       SELECT c,p,
                              CASE WHEN %s::double precision IS NULL THEN c ELSE ST_ReducePrecision(c,%s) END AS ec,
                              CASE WHEN %s::double precision IS NULL THEN p ELSE ST_ReducePrecision(p,%s) END AS ep
                       FROM raw
                   )
                   SELECT ST_IsValid(p) AND NOT ST_IsEmpty(p) AND ST_SRID(p)=4326,
                          CASE WHEN ST_Intersects(c,p) THEN ST_Area(ST_Intersection(c,p)::geography) ELSE 0 END,
                          CASE WHEN ST_Intersects(ec,ep) THEN ST_Area(ST_Intersection(ec,ep)::geography) ELSE 0 END
                   FROM eval""",
                (candidate_wkb_hex, peer_wkb_hex, grid, grid, grid, grid),
            )
            row = cur.fetchone()
        if row is None:
            raise CityQualificationError("PostGIS peer qualification returned no result")
        return bool(row[0]), float(row[1]), float(row[2])

    def _city_affecting_residual_count(self, city_id: str) -> int:
        """Read D3 residual evidence when migration 22 exists; pre-migration returns zero."""
        with self.connection.cursor() as cur:
            cur.execute("SELECT to_regclass('geography.nngla_unresolved_territorial_residual')")
            exists = cur.fetchone()
            if not exists or exists[0] is None:
                return 0
            cur.execute(
                """SELECT count(*) FROM geography.nngla_unresolved_territorial_residual
                   WHERE parent_administrative_area_id=%s AND review_status='REVIEW_DEFERRED'
                     AND affects_feature_boundary=true""",
                (city_id,),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def qualify(
        self,
        city_administrative_area_id: str,
        *, qualifier_actor_id: str,
        candidate_source_mode: CandidateSourceMode = CandidateSourceMode.FROZEN_SOURCE_REUSE,
        fabric_run_id: str = "",
        precision_policy: PrecisionPolicy = SOURCE_EXACT_PRECISION,
        enforce_read_only_transaction: bool = True,
    ) -> CityQualificationReceipt:
        if not qualifier_actor_id.strip():
            raise ValueError("qualifier actor is required")
        if enforce_read_only_transaction:
            with self.connection.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
        root = _city_root_for_admin(city_administrative_area_id)
        candidate = (
            self.resolver.frozen_candidate(city_administrative_area_id)
            if candidate_source_mode is CandidateSourceMode.FROZEN_SOURCE_REUSE
            else self.resolver.delivery2_candidate(city_administrative_area_id, fabric_run_id)
        )
        parent = self.resolver.validation_evidence(root.validation_parent_id, root.place_id)
        peers = self.resolver.peers(city_administrative_area_id, root.validation_parent_id, root.place_id)
        point = administrative_reference_seed(city_administrative_area_id)
        pair = self._evaluate_pair(candidate, parent, longitude=point.longitude, latitude=point.latitude, policy=precision_policy)

        raw_city_peer_overlap = 0.0
        city_peer_overlap = 0.0
        raw_municipality_overlap = 0.0
        municipality_overlap = 0.0
        peer_valid = True
        peer_material = []
        for peer in peers:
            valid, raw_overlap, evaluated_overlap = self._peer_overlap(candidate.geometry_wkb_hex, peer.geometry_wkb_hex, precision_policy)
            peer_valid = peer_valid and valid
            if peer.administrative_type_code == "CITY":
                raw_city_peer_overlap += raw_overlap
                city_peer_overlap += evaluated_overlap
            elif peer.administrative_type_code == "MUNICIPALITY":
                # Municipality overlap is validation evidence. It is reported separately
                # and never converted into an all-siblings completeness prerequisite.
                raw_municipality_overlap += raw_overlap
                municipality_overlap += evaluated_overlap
            peer_material.append({
                "subjectId": peer.subject_id,
                "type": peer.administrative_type_code,
                "evidenceKind": peer.evidence_kind,
                "evidenceId": peer.evidence_id,
                "geometrySha256": peer.geometry_sha256,
                "qualificationReference": peer.qualification_reference,
                "rawOverlapM2": raw_overlap,
                "evaluatedOverlapM2": evaluated_overlap,
            })

        unresolved = self._city_affecting_residual_count(city_administrative_area_id)
        raw_candidate_sha = _sha_wkb_hex(pair.raw_candidate_wkb_hex)
        evaluated_candidate_sha = _sha_wkb_hex(pair.evaluated_candidate_wkb_hex)
        raw_parent_sha = _sha_wkb_hex(pair.raw_parent_wkb_hex)
        evaluated_parent_sha = _sha_wkb_hex(pair.evaluated_parent_wkb_hex)
        peer_digest = stable_digest(peer_material)
        source_bound = bool(candidate.source_geometry_sha256 and candidate.source_path_reference and candidate.candidate_id)

        failed: list[str] = []
        blocked_by_evidence = False
        reconstruction = False
        if not pair.polygonal:
            failed.append("CITY_NOT_POLYGONAL"); reconstruction = True
        if not pair.non_empty:
            failed.append("CITY_EMPTY"); reconstruction = True
        if not pair.valid_geometry:
            failed.append("CITY_INVALID"); reconstruction = True
        if not pair.srid_correct:
            failed.append("CITY_CRS_INVALID"); reconstruction = True
        if not pair.parent_evidence_valid:
            failed.append("VALIDATION_PARENT_EVIDENCE_INVALID"); blocked_by_evidence = True
        if not peer_valid:
            failed.append("PEER_EVIDENCE_INVALID"); blocked_by_evidence = True
        if not pair.city_covered_by_parent or pair.area_outside_parent_m2 != 0.0:
            failed.append("CITY_PARENT_CONTAINMENT_FAILED"); reconstruction = True
        if city_peer_overlap != 0.0:
            failed.append("CITY_POSITIVE_CITY_PEER_OVERLAP"); blocked_by_evidence = True
        if not pair.reference_point_covered:
            failed.append("CITY_REFERENCE_POINT_NOT_COVERED"); reconstruction = True
        if unresolved:
            failed.append("UNRESOLVED_CITY_AFFECTING_DEFECT"); blocked_by_evidence = True
        if not source_bound:
            failed.append("CITY_PROVENANCE_UNBOUND"); blocked_by_evidence = True

        if blocked_by_evidence:
            status = CityQualificationStatus.CITY_BLOCKED_BY_EVIDENCE
        elif reconstruction:
            status = CityQualificationStatus.CITY_RECONSTRUCTION_REQUIRED
        else:
            status = CityQualificationStatus.CITY_READY_FOR_AUTHORITY

        residue = (
            numerical_residue(raw_value=pair.raw_area_outside_parent_m2, evaluated_value=pair.area_outside_parent_m2, policy=precision_policy)
            or numerical_residue(raw_value=raw_city_peer_overlap, evaluated_value=city_peer_overlap, policy=precision_policy)
        )
        qualification_id = stable_id("city-qualification:nngla:", {
            "city": city_administrative_area_id,
            "candidate": candidate.candidate_id,
            "rawCandidateSha256": raw_candidate_sha,
            "parent": parent.subject_id,
            "parentSha256": raw_parent_sha,
            "peers": peer_digest,
            "precision": precision_policy.policy_sha256,
            "qualifier": qualifier_actor_id,
        })
        receipt = CityQualificationReceipt(
            qualification_id=qualification_id,
            city_administrative_area_id=city_administrative_area_id,
            root_place_id=root.place_id,
            candidate_source_mode=candidate.candidate_source_mode,
            candidate_id=candidate.candidate_id,
            raw_candidate_geometry_sha256=raw_candidate_sha,
            evaluated_candidate_geometry_sha256=evaluated_candidate_sha,
            source_geometry_sha256=candidate.source_geometry_sha256,
            source_dataset_id=candidate.source_dataset_id,
            source_dataset_version=candidate.source_dataset_version,
            source_path_reference=candidate.source_path_reference,
            fabric_run_id=candidate.fabric_run_id,
            package_sha256=candidate.package_sha256,
            validation_parent_id=parent.subject_id,
            parent_evidence_kind=parent.evidence_kind,
            parent_evidence_id=parent.evidence_id,
            raw_parent_geometry_sha256=raw_parent_sha,
            evaluated_parent_geometry_sha256=evaluated_parent_sha,
            parent_qualification_reference=parent.qualification_reference,
            parent_source_path_reference=parent.source_path_reference,
            peer_evidence_digest=peer_digest,
            precision_policy_id=precision_policy.policy_id,
            precision_policy_sha256=precision_policy.policy_sha256,
            precision_mode=precision_policy.mode,
            precision_grid_size_degrees=precision_policy.grid_size_degrees,
            precision_evidence_reference=precision_policy.evidence_reference,
            valid_geometry=pair.valid_geometry,
            polygonal=pair.polygonal,
            non_empty=pair.non_empty,
            srid_correct=pair.srid_correct,
            parent_evidence_valid=pair.parent_evidence_valid and peer_valid,
            city_covered_by_parent=pair.city_covered_by_parent,
            raw_area_outside_parent_m2=pair.raw_area_outside_parent_m2,
            area_outside_parent_m2=pair.area_outside_parent_m2,
            raw_positive_city_peer_overlap_m2=raw_city_peer_overlap,
            positive_city_peer_overlap_m2=city_peer_overlap,
            raw_positive_municipality_overlap_m2=raw_municipality_overlap,
            positive_municipality_overlap_m2=municipality_overlap,
            reference_point_covered=pair.reference_point_covered,
            unresolved_city_affecting_defect_count=unresolved,
            numerical_residue=residue,
            source_provenance_bound=source_bound,
            qualifier_actor_id=qualifier_actor_id,
            runtime_mode="production",
            status=status,
            failed_predicates=tuple(failed),
            database_mutation=False,
        )
        if enforce_read_only_transaction:
            self.connection.rollback()
        return receipt


__all__ = [
    "CityQualificationError", "PostgreSQLCityEvidenceResolver", "PostgreSQLCityFeatureQualifier",
]
