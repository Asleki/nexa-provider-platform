"""Geometry-derived PostGIS qualification and exact R3 successor reconciliation.

Historical Bundle 19B PASS flags remain provenance, not executable topology truth.
R3 preserves every raw predicate failure, characterizes its residual, and permits
only policy-eligible micro defects to produce a new successor fabric.  The final
successor is then re-qualified exactly; tolerance never becomes a topology PASS.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from .contracts import (
    AssessmentStage,
    CityClosure,
    FindingSeverity,
    FindingStatus,
    GeometryCandidate,
    GeometryEncoding,
    GeometryRole,
    RepairMode,
    TopologyAssessment,
    TopologyFinding,
)
from .partition_reconciliation import PartitionReconciliationError, reconcile_city_partition
from .residual_policy import (
    MAX_AUTOMATIC_RESIDUAL_KM2,
    MAX_AUTOMATIC_RESIDUAL_RATIO,
    RepairEligibility,
    ResidualClass,
    context_decision,
    executable_decision,
)

TOPOLOGY_POLICY_ID = "nngla-spatial-realization-topology-v2"
REPAIR_POLICY_ID = "nngla-exact-partition-edge-reconciliation-v2"
DIAGNOSTIC_EQUAL_AREA_SRID = 6933

_REPAIRABLE_CODES = {
    "SOVEREIGN_CONTAINMENT_FAILED",
    "CITY_PARENT_CONTAINMENT_FAILED",
    "DISTRICT_PARENT_CONTAINMENT_FAILED",
    "CITY_DISTRICT_GAP",
    "CITY_DISTRICT_OVERSHOOT",
    "CITY_DISTRICT_POSITIVE_OVERLAP",
}


def _stable_id(prefix: str, *parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts).encode()
    return prefix + sha256(material).hexdigest()


def _candidate_values(candidates: Iterable[GeometryCandidate]):
    rows = tuple(candidates)
    if not rows:
        raise ValueError("at least one geometry candidate is required")
    sql = ",".join(["(%s,%s,%s)"] * len(rows))
    params: list[str] = []
    for item in rows:
        params.extend((item.subject_id, item.encoding.value, item.payload))
    cte = (
        "raw(subject_id,encoding,payload) AS (VALUES " + sql + "), "
        "geom AS (SELECT subject_id, CASE WHEN encoding='GEOJSON' "
        "THEN ST_SetSRID(ST_GeomFromGeoJSON(payload),4326) "
        "ELSE ST_GeomFromEWKB(decode(payload,'hex')) END AS geometry FROM raw)"
    )
    return cte, tuple(params)


def _finding(
    root_id: str,
    code: str,
    severity: FindingSeverity,
    subject_id: str,
    *,
    stage: AssessmentStage = AssessmentStage.SOURCE_CANDIDATE,
    related: str = "",
    role: str = "",
    predicate: str = "",
    expected: str = "",
    actual: str = "",
    raw_predicate_result: str = "",
    difference_dimension: int | None = None,
    area_km2: float | None = None,
    area_ratio: float | None = None,
    residual_class: str = ResidualClass.NONE.value,
    bbox: str = "",
    point: str = "",
    repair_eligibility: str = RepairEligibility.NOT_APPLICABLE.value,
    repair_strategy: str = "",
) -> TopologyFinding:
    fid = _stable_id(
        "finding:nngla:spatial-realization:",
        root_id, stage.value, code, subject_id, related, role, predicate, actual,
    )
    return TopologyFinding(
        finding_id=fid,
        root_place_id=root_id,
        rule_code=code,
        severity=severity,
        status=FindingStatus.OPEN,
        subject_id=subject_id,
        related_subject_id=related,
        geometry_role=role,
        predicate=predicate,
        expected=expected,
        actual=actual,
        assessment_stage=stage,
        raw_predicate_result=raw_predicate_result,
        difference_dimension=difference_dimension,
        measurement_method=(f"EPSG:{DIAGNOSTIC_EQUAL_AREA_SRID}_EQUAL_AREA" if area_km2 is not None else ""),
        area_km2=area_km2,
        area_ratio=area_ratio,
        residual_class=residual_class,
        difference_bbox=bbox,
        representative_point=point,
        repair_eligibility=repair_eligibility,
        repair_strategy=repair_strategy,
    )


class PostGISSpatialTopologyEngine:
    """Recompute selected-city topology against live PostGIS Boundary v2."""

    def __init__(self, connection, *, repair_mode: RepairMode | str = RepairMode.SAFE_AUTOMATIC) -> None:
        self.connection = connection
        self.repair_mode = RepairMode(repair_mode)

    def assess(self, closure: CityClosure) -> TopologyAssessment:
        original = tuple(closure.desired_candidates)
        raw = self._assess_once(closure, original, stage=AssessmentStage.SOURCE_CANDIDATE)
        if not raw.blocking_findings:
            return raw
        if not self._repair_eligible(closure, raw):
            return raw
        try:
            repaired = self._repair_selected_fabric(closure, original)
        except PartitionReconciliationError as exc:
            failure = _finding(
                closure.root.place_id,
                "SUCCESSOR_PARTITION_RECONCILIATION_FAILED",
                FindingSeverity.BLOCKING,
                closure.root.administrative_area_id,
                stage=AssessmentStage.SUCCESSOR_CANDIDATE,
                predicate="canonical_seed_shared_partition",
                expected="deterministic_exact_successor",
                actual=str(exc),
                repair_eligibility=RepairEligibility.NOT_APPLICABLE.value,
                repair_strategy=REPAIR_POLICY_ID,
            )
            return TopologyAssessment(
                closure.root.place_id,
                original,
                raw.findings + (failure,),
                repair_applied=False,
            )
        verified = self._assess_once(closure, repaired, stage=AssessmentStage.SUCCESSOR_CANDIDATE)
        source_findings = tuple(item.superseded() if item.blocking else item for item in raw.findings)
        if verified.blocking_findings:
            return TopologyAssessment(
                closure.root.place_id,
                repaired,
                source_findings + verified.findings,
                repair_applied=True,
            )
        info = _finding(
            closure.root.place_id,
            "EXACT_TOPOLOGY_SUCCESSOR_RECONCILIATION_APPLIED",
            FindingSeverity.INFO,
            closure.root.administrative_area_id,
            stage=AssessmentStage.SUCCESSOR_CANDIDATE,
            predicate="successor_reverification",
            expected="PASS",
            actual="PASS",
            raw_predicate_result="true",
            repair_eligibility="APPLIED",
            repair_strategy=f"{REPAIR_POLICY_ID}:{self.repair_mode.value}",
        )
        return TopologyAssessment(
            closure.root.place_id,
            repaired,
            source_findings + verified.findings + (info,),
            repair_applied=True,
        )

    def _assess_once(
        self,
        closure: CityClosure,
        candidates: tuple[GeometryCandidate, ...],
        *,
        stage: AssessmentStage,
    ) -> TopologyAssessment:
        by_key = {(item.subject_id, item.geometry_role): item for item in candidates}
        city = by_key[(closure.admin_root.subject_id, GeometryRole.ADMINISTRATIVE_BOUNDARY)]
        districts = tuple(
            by_key[(item.subject_id, GeometryRole.ADMINISTRATIVE_BOUNDARY)]
            for item in closure.exhaustive_children
        )
        point = by_key[(closure.place_reference.subject_id, GeometryRole.PLACE_REFERENCE_POINT)]
        footprint = None
        if closure.settlement_footprint is not None:
            footprint = by_key[(closure.settlement_footprint.subject_id, GeometryRole.SETTLEMENT_FOOTPRINT)]
        findings: list[TopologyFinding] = []
        findings.extend(self._basic_and_sovereign(closure, candidates, stage=stage))
        findings.extend(self._seed_validation(closure, city, stage=stage))
        findings.extend(self._place_relations(closure, point, footprint, city, stage=stage))
        findings.extend(self._city_parent(closure, city, stage=stage))
        findings.extend(self._district_partition(closure, city, districts, stage=stage))
        findings.extend(self._overlay_context(closure, city, stage=stage))
        findings.extend(self._regional_context(closure, city, stage=stage))
        return TopologyAssessment(closure.root.place_id, candidates, tuple(findings), repair_applied=False)

    def _candidate_role(self, closure: CityClosure, candidates, subject_id: str, gtype: str):
        matches = [item for item in candidates if item.subject_id == subject_id]
        if len(matches) == 1:
            return matches[0]
        expected = {
            "ST_Point": GeometryRole.PLACE_REFERENCE_POINT,
            "ST_Polygon": GeometryRole.SETTLEMENT_FOOTPRINT,
            "ST_MultiPolygon": GeometryRole.SETTLEMENT_FOOTPRINT,
        }.get(gtype)
        if subject_id == closure.root.place_id and expected is not None:
            for item in matches:
                if item.geometry_role is expected:
                    return item
        return matches[0] if matches else None

    def _basic_and_sovereign(self, closure: CityClosure, candidates, *, stage: AssessmentStage):
        context_rows = candidates + (closure.validation_parent,) + closure.overlays + closure.regional_partition_peers
        context_by_key = {}
        for item in context_rows:
            context_by_key.setdefault((item.subject_id, item.geometry_role, item.geometry_type_code), item)
        context = tuple(context_by_key.values())
        cte, params = _candidate_values(context)
        sql = f"""
        WITH {cte}, sovereign AS (
          SELECT geometry FROM geography.world_boundary_version
          WHERE boundary_id='boundary:novegeo:sovereign' AND boundary_version=2
            AND lifecycle_status='active'
          LIMIT 1
        ), evaluated AS (
          SELECT g.subject_id,g.geometry,
                 ST_IsValid(g.geometry) AS valid,
                 NOT ST_IsEmpty(g.geometry) AS nonempty,
                 ST_SRID(g.geometry) AS srid,
                 ST_GeometryType(g.geometry) AS gtype,
                 ST_CoveredBy(g.geometry,s.geometry) AS covered,
                 ST_Difference(g.geometry,s.geometry) AS outside_geometry
          FROM geom g CROSS JOIN sovereign s
        )
        SELECT subject_id,valid,nonempty,srid,gtype,covered,
               ST_IsEmpty(outside_geometry),ST_Dimension(outside_geometry),
               ST_Area(ST_Transform(outside_geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               ST_AsText(ST_Envelope(outside_geometry)),
               CASE WHEN ST_IsEmpty(outside_geometry) THEN '' ELSE ST_AsText(ST_PointOnSurface(outside_geometry)) END
        FROM evaluated ORDER BY subject_id,gtype
        """
        with self.connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        desired_keys = {(item.subject_id, item.geometry_role, item.geometry_type_code) for item in candidates}
        out = []
        for row in rows:
            subject_id, valid, nonempty, srid, gtype, covered, diff_empty, diff_dimension, diff_area, subject_area, bbox, point = row
            subject_id = str(subject_id); gtype = str(gtype)
            candidate = self._candidate_role(closure, candidates, subject_id, gtype)
            role = candidate.geometry_role.value if candidate is not None else GeometryRole.ADMINISTRATIVE_BOUNDARY.value
            is_executable = candidate is not None and (candidate.subject_id, candidate.geometry_role, candidate.geometry_type_code) in desired_keys
            base_severity = FindingSeverity.BLOCKING if is_executable else FindingSeverity.WARNING
            if not bool(valid):
                out.append(_finding(closure.root.place_id,"GEOMETRY_INVALID",base_severity,subject_id,stage=stage,role=role,predicate="ST_IsValid",expected="true",actual="false",raw_predicate_result="false"))
            if not bool(nonempty):
                out.append(_finding(closure.root.place_id,"GEOMETRY_EMPTY",base_severity,subject_id,stage=stage,role=role,predicate="NOT ST_IsEmpty",expected="true",actual="false",raw_predicate_result="false"))
            if int(srid) != 4326:
                out.append(_finding(closure.root.place_id,"CRS_MISMATCH",base_severity,subject_id,stage=stage,role=role,predicate="ST_SRID",expected="4326",actual=str(srid),raw_predicate_result=str(srid)))
            if gtype not in {"ST_Point", "ST_Polygon", "ST_MultiPolygon"}:
                out.append(_finding(closure.root.place_id,"GEOMETRY_TYPE_UNSUPPORTED",base_severity,subject_id,stage=stage,role=role,predicate="ST_GeometryType",expected="POINT/POLYGON/MULTIPOLYGON",actual=gtype,raw_predicate_result=gtype))
            if bool(covered):
                continue
            area = float(diff_area or 0.0); total = float(subject_area or 0.0); ratio = area / total if total > 0 else 0.0
            dimension = None if diff_dimension is None else int(diff_dimension)
            if not is_executable:
                decision = context_decision(area_km2=area, area_ratio=ratio, difference_dimension=dimension)
                severity = FindingSeverity.WARNING
            elif gtype == "ST_Point" or role == GeometryRole.SETTLEMENT_FOOTPRINT.value:
                decision = None
                severity = FindingSeverity.BLOCKING
            else:
                decision = executable_decision(area_km2=area, area_ratio=ratio, difference_dimension=dimension)
                severity = FindingSeverity.BLOCKING
            residual_class = decision.residual_class.value if decision is not None else ResidualClass.MATERIAL_TOPOLOGY_FAILURE.value
            eligibility = decision.repair_eligibility.value if decision is not None else RepairEligibility.NOT_APPLICABLE.value
            out.append(_finding(
                closure.root.place_id,"SOVEREIGN_CONTAINMENT_FAILED",severity,subject_id,
                stage=stage,role=role,predicate="ST_CoveredBy(subject,BoundaryV2)",expected="true",actual=f"false;ratio={ratio:.12g}",raw_predicate_result="false",
                difference_dimension=dimension,area_km2=area,area_ratio=ratio,residual_class=residual_class,
                bbox=str(bbox or ""),point=str(point or ""),repair_eligibility=eligibility,
                repair_strategy=REPAIR_POLICY_ID if eligibility==RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE.value else "",
            ))
        if not rows:
            out.append(_finding(closure.root.place_id,"ACTIVE_SOVEREIGN_BOUNDARY_UNAVAILABLE",FindingSeverity.BLOCKING,closure.root.place_id,stage=stage,predicate="BoundaryV2",expected="active",actual="missing"))
        return out

    def _seed_validation(self, closure: CityClosure, city: GeometryCandidate, *, stage: AssessmentStage):
        city_expr, city_params = self._geometry_expression(city)
        values = []
        placeholders = []
        for seed in closure.exhaustive_child_seeds:
            placeholders.append("(%s,%s,%s)")
            values.extend((seed.subject_id,float(seed.longitude),float(seed.latitude)))
        sql = f"""
        WITH seeds(subject_id,longitude,latitude) AS (VALUES {','.join(placeholders)}),
        city AS (SELECT {city_expr} AS geometry)
        SELECT s.subject_id,ST_CoveredBy(ST_SetSRID(ST_MakePoint(s.longitude,s.latitude),4326),c.geometry)
        FROM seeds s CROSS JOIN city c ORDER BY s.subject_id
        """
        with self.connection.cursor() as cur:
            cur.execute(sql, tuple(values)+tuple(city_params))
            rows = cur.fetchall()
        by_id = {str(row[0]): bool(row[1]) for row in rows}
        out=[]
        for seed in closure.exhaustive_child_seeds:
            if by_id.get(seed.subject_id) is True:
                continue
            out.append(_finding(
                closure.root.place_id,"DISTRICT_REFERENCE_SEED_INVALID",FindingSeverity.BLOCKING,seed.subject_id,
                stage=stage,related=city.subject_id,predicate="ST_CoveredBy(canonical_child_seed,city)",expected="true",actual="false",raw_predicate_result="false",
                repair_eligibility=RepairEligibility.NOT_APPLICABLE.value,
            ))
        return out

    @staticmethod
    def _geometry_expression(candidate: GeometryCandidate):
        if candidate.encoding is GeometryEncoding.GEOJSON:
            return "ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)", (candidate.payload,)
        return "ST_GeomFromEWKB(decode(%s,'hex'))", (candidate.payload,)

    def _place_relations(self, closure, point, footprint, city, *, stage):
        psql, pp = self._geometry_expression(point); csql, cp = self._geometry_expression(city)
        if footprint is not None:
            fsql, fp = self._geometry_expression(footprint)
            query=f"SELECT ST_CoveredBy({psql},{csql}), ST_CoveredBy({psql},{fsql})"; values=pp+cp+pp+fp
        else:
            query=f"SELECT ST_CoveredBy({psql},{csql}), true"; values=pp+cp
        with self.connection.cursor() as cur:
            cur.execute(query,values); row=cur.fetchone()
        out=[]
        if row is None or not bool(row[0]):
            out.append(_finding(closure.root.place_id,"REFERENCE_POINT_NOT_COVERED_BY_CITY",FindingSeverity.BLOCKING,point.subject_id,stage=stage,related=city.subject_id,role=GeometryRole.PLACE_REFERENCE_POINT.value,predicate="ST_CoveredBy(point,city)",expected="true",actual="false",raw_predicate_result="false"))
        if row is None or not bool(row[1]):
            out.append(_finding(closure.root.place_id,"REFERENCE_POINT_NOT_COVERED_BY_FOOTPRINT",FindingSeverity.BLOCKING,point.subject_id,stage=stage,related=point.subject_id,role=GeometryRole.SETTLEMENT_FOOTPRINT.value,predicate="ST_CoveredBy(point,footprint)",expected="true",actual="false",raw_predicate_result="false"))
        return out

    def _difference_metrics(self, subject: GeometryCandidate, parent: GeometryCandidate):
        ssql, sp = self._geometry_expression(subject); psql, pp = self._geometry_expression(parent)
        query=f"""
        WITH x AS (SELECT {ssql} AS child, {psql} AS parent),
        d AS (SELECT ST_Difference(child,parent) AS geom,parent FROM x)
        SELECT ST_IsEmpty(geom),
               ST_Area(ST_Transform(geom,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               ST_Area(ST_Transform(parent,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               ST_Dimension(geom),ST_AsText(ST_Envelope(geom)),
               CASE WHEN ST_IsEmpty(geom) THEN '' ELSE ST_AsText(ST_PointOnSurface(geom)) END
        FROM d
        """
        with self.connection.cursor() as cur:
            cur.execute(query,sp+pp); return cur.fetchone()

    def _residual_rule_finding(self, closure, code, subject_id, related, row, *, stage, predicate):
        empty, area, parent_area, dimension, bbox, point = row
        if bool(empty):
            return None
        area=float(area or 0.0); parent_area=float(parent_area or 0.0); ratio=area/parent_area if parent_area>0 else 0.0
        decision=executable_decision(area_km2=area,area_ratio=ratio,difference_dimension=None if dimension is None else int(dimension))
        return _finding(
            closure.root.place_id,code,FindingSeverity.BLOCKING,subject_id,stage=stage,related=related,
            predicate=predicate,expected="true",actual=f"false;ratio={ratio:.12g}",raw_predicate_result="false",
            difference_dimension=None if dimension is None else int(dimension),area_km2=area,area_ratio=ratio,residual_class=decision.residual_class.value,
            bbox=str(bbox or ""),point=str(point or ""),repair_eligibility=decision.repair_eligibility.value,
            repair_strategy=REPAIR_POLICY_ID if decision.repair_eligibility is RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE else "",
        )

    def _city_parent(self, closure: CityClosure, city: GeometryCandidate, *, stage):
        row=self._difference_metrics(city,closure.validation_parent)
        if row is None:
            return (_finding(closure.root.place_id,"CITY_PARENT_CONTAINMENT_UNRESOLVED",FindingSeverity.BLOCKING,city.subject_id,stage=stage,related=closure.validation_parent.subject_id,actual="no-result"),)
        finding=self._residual_rule_finding(closure,"CITY_PARENT_CONTAINMENT_FAILED",city.subject_id,closure.validation_parent.subject_id,row,stage=stage,predicate="ST_IsEmpty(ST_Difference(city,parent))")
        return () if finding is None else (finding,)

    def _district_partition(self, closure, city, districts, *, stage):
        candidates=(city,)+tuple(districts); cte,params=_candidate_values(candidates)
        child_ids=tuple(item.subject_id for item in districts); placeholders=','.join(['%s']*len(child_ids))
        sql=f"""
        WITH {cte}, parent AS (SELECT geometry FROM geom WHERE subject_id=%s),
        children AS (SELECT subject_id,geometry FROM geom WHERE subject_id IN ({placeholders})),
        u AS (SELECT ST_UnaryUnion(ST_Collect(geometry)) geometry FROM children),
        gap AS (SELECT ST_Difference(parent.geometry,u.geometry) geometry,parent.geometry parent FROM parent CROSS JOIN u),
        over AS (SELECT ST_Difference(u.geometry,parent.geometry) geometry,parent.geometry parent FROM parent CROSS JOIN u),
        peer_overlaps AS (
          SELECT a.subject_id a_id,b.subject_id b_id,ST_Intersection(a.geometry,b.geometry) geometry
          FROM children a JOIN children b ON a.subject_id<b.subject_id
        )
        SELECT
          (SELECT ST_IsEmpty(geometry) FROM gap),(SELECT ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0 FROM gap),(SELECT ST_Dimension(geometry) FROM gap),(SELECT ST_AsText(ST_Envelope(geometry)) FROM gap),(SELECT CASE WHEN ST_IsEmpty(geometry) THEN '' ELSE ST_AsText(ST_PointOnSurface(geometry)) END FROM gap),
          (SELECT ST_IsEmpty(geometry) FROM over),(SELECT ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0 FROM over),(SELECT ST_Dimension(geometry) FROM over),(SELECT ST_AsText(ST_Envelope(geometry)) FROM over),(SELECT CASE WHEN ST_IsEmpty(geometry) THEN '' ELSE ST_AsText(ST_PointOnSurface(geometry)) END FROM over),
          (SELECT COALESCE(SUM(ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0),0) FROM peer_overlaps WHERE NOT ST_IsEmpty(geometry) AND ST_Dimension(geometry)=2),
          (SELECT COUNT(*) FROM peer_overlaps WHERE NOT ST_IsEmpty(geometry) AND ST_Dimension(geometry)=2),
          (SELECT ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0 FROM parent)
        """
        with self.connection.cursor() as cur:
            cur.execute(sql,tuple(params)+(city.subject_id,)+child_ids); metrics=cur.fetchone()
        if metrics is None:
            return (_finding(closure.root.place_id,"CITY_DISTRICT_PARTITION_UNRESOLVED",FindingSeverity.BLOCKING,city.subject_id,stage=stage,actual="no-result"),)
        gap_empty,gap_area,gap_dim,gap_bbox,gap_point,over_empty,over_area,over_dim,over_bbox,over_point,overlap_area,overlap_count,parent_area=metrics
        parent_area=float(parent_area or 0.0); out=[]
        for child in districts:
            row=self._difference_metrics(child,city)
            if row is None: continue
            finding=self._residual_rule_finding(closure,"DISTRICT_PARENT_CONTAINMENT_FAILED",child.subject_id,city.subject_id,row,stage=stage,predicate="ST_IsEmpty(ST_Difference(child,city))")
            if finding is not None: out.append(finding)
        def add_partition(code,empty,area,dimension,bbox,point,predicate):
            if bool(empty): return
            a=float(area or 0.0); ratio=a/parent_area if parent_area>0 else 0.0
            decision=executable_decision(area_km2=a,area_ratio=ratio,difference_dimension=None if dimension is None else int(dimension))
            out.append(_finding(closure.root.place_id,code,FindingSeverity.BLOCKING,city.subject_id,stage=stage,predicate=predicate,expected="true",actual=f"false;ratio={ratio:.12g}",raw_predicate_result="false",difference_dimension=None if dimension is None else int(dimension),area_km2=a,area_ratio=ratio,residual_class=decision.residual_class.value,bbox=str(bbox or ""),point=str(point or ""),repair_eligibility=decision.repair_eligibility.value,repair_strategy=REPAIR_POLICY_ID if decision.repair_eligibility is RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE else ""))
        add_partition("CITY_DISTRICT_GAP",gap_empty,gap_area,gap_dim,gap_bbox,gap_point,"ST_IsEmpty(city - union(districts))")
        add_partition("CITY_DISTRICT_OVERSHOOT",over_empty,over_area,over_dim,over_bbox,over_point,"ST_IsEmpty(union(districts) - city)")
        if int(overlap_count or 0)>0:
            a=float(overlap_area or 0.0); ratio=a/parent_area if parent_area>0 else 0.0
            decision=executable_decision(area_km2=a,area_ratio=ratio,difference_dimension=2 if a>0 else 1)
            out.append(_finding(closure.root.place_id,"CITY_DISTRICT_POSITIVE_OVERLAP",FindingSeverity.BLOCKING,city.subject_id,stage=stage,predicate="ST_Dimension(intersection(peer,peer))<2",expected="true",actual=f"false;pairs={int(overlap_count)};ratio={ratio:.12g}",raw_predicate_result="false",difference_dimension=2 if a>0 else 1,area_km2=a,area_ratio=ratio,residual_class=decision.residual_class.value,repair_eligibility=decision.repair_eligibility.value,repair_strategy=REPAIR_POLICY_ID if decision.repair_eligibility is RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE else ""))
        return tuple(out)

    def _overlay_context(self, closure, city, *, stage):
        out=[]
        for overlay in closure.overlays:
            row=self._difference_metrics(overlay,city)
            if row is None or bool(row[0]): continue
            area=float(row[1] or 0.0); parent_area=float(row[2] or 0.0); ratio=area/parent_area if parent_area>0 else 0.0
            out.append(_finding(closure.root.place_id,"OVERLAY_PARENT_CONTAINMENT_CONTEXT",FindingSeverity.WARNING,overlay.subject_id,stage=stage,related=city.subject_id,predicate="ST_IsEmpty(ST_Difference(overlay,city))",expected="true",actual="false",raw_predicate_result="false",difference_dimension=None if row[3] is None else int(row[3]),area_km2=area,area_ratio=ratio,residual_class=context_decision(area_km2=area,area_ratio=ratio,difference_dimension=None if row[3] is None else int(row[3])).residual_class.value,bbox=str(row[4] or ""),point=str(row[5] or ""),repair_eligibility="NOT_EXECUTED_IN_CITY_PILOT"))
        return tuple(out)

    def _regional_context(self, closure, selected_city, *, stage):
        peers=[selected_city if item.subject_id==selected_city.subject_id else item for item in closure.regional_partition_peers]
        cte,params=_candidate_values((closure.validation_parent,)+tuple(peers)); ids=tuple(item.subject_id for item in peers); placeholders=','.join(['%s']*len(ids))
        sql=f"""
        WITH {cte}, parent AS (SELECT geometry FROM geom WHERE subject_id=%s),
        children AS (SELECT subject_id,geometry FROM geom WHERE subject_id IN ({placeholders})),
        u AS (SELECT ST_UnaryUnion(ST_Collect(geometry)) geometry FROM children),
        gap AS (SELECT ST_Difference(parent.geometry,u.geometry) geometry FROM parent CROSS JOIN u),
        over AS (SELECT ST_Difference(u.geometry,parent.geometry) geometry FROM parent CROSS JOIN u),
        peer_overlaps AS (SELECT ST_Intersection(a.geometry,b.geometry) geometry FROM children a JOIN children b ON a.subject_id<b.subject_id)
        SELECT ST_IsEmpty((SELECT geometry FROM gap)),ST_Area(ST_Transform((SELECT geometry FROM gap),{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               ST_IsEmpty((SELECT geometry FROM over)),ST_Area(ST_Transform((SELECT geometry FROM over),{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0,
               (SELECT COUNT(*) FROM peer_overlaps WHERE NOT ST_IsEmpty(geometry) AND ST_Dimension(geometry)=2),
               (SELECT COALESCE(SUM(ST_Area(ST_Transform(geometry,{DIAGNOSTIC_EQUAL_AREA_SRID}))/1000000.0),0) FROM peer_overlaps WHERE NOT ST_IsEmpty(geometry) AND ST_Dimension(geometry)=2)
        """
        with self.connection.cursor() as cur:
            cur.execute(sql,tuple(params)+(closure.validation_parent.subject_id,)+ids); row=cur.fetchone()
        out=[]
        if row is None:return tuple(out)
        if not bool(row[0]):out.append(_finding(closure.root.place_id,"REGIONAL_CONTEXT_GAP",FindingSeverity.WARNING,closure.validation_parent.subject_id,stage=stage,predicate="ST_IsEmpty(region - union(peers))",expected="true",actual="false",raw_predicate_result="false",area_km2=float(row[1] or 0.0),repair_eligibility=RepairEligibility.CONTEXT_ONLY.value))
        if not bool(row[2]):out.append(_finding(closure.root.place_id,"REGIONAL_CONTEXT_OVERSHOOT",FindingSeverity.WARNING,closure.validation_parent.subject_id,stage=stage,predicate="ST_IsEmpty(union(peers) - region)",expected="true",actual="false",raw_predicate_result="false",area_km2=float(row[3] or 0.0),repair_eligibility=RepairEligibility.CONTEXT_ONLY.value))
        if int(row[4] or 0)>0:out.append(_finding(closure.root.place_id,"REGIONAL_CONTEXT_POSITIVE_OVERLAP",FindingSeverity.WARNING,closure.validation_parent.subject_id,stage=stage,predicate="peer overlap dimension",expected="<2",actual=f"pairs={int(row[4])}",raw_predicate_result="false",area_km2=float(row[5] or 0.0),repair_eligibility=RepairEligibility.CONTEXT_ONLY.value))
        for peer in peers:
            if peer.subject_id==selected_city.subject_id:continue
            r=self._difference_metrics(peer,closure.validation_parent)
            if r is not None and not bool(r[0]):
                area=float(r[1] or 0.0); parent_area=float(r[2] or 0.0); ratio=area/parent_area if parent_area>0 else 0.0
                decision=context_decision(area_km2=area,area_ratio=ratio,difference_dimension=None if r[3] is None else int(r[3]))
                out.append(_finding(closure.root.place_id,"REGIONAL_CONTEXT_PARENT_CONTAINMENT",FindingSeverity.WARNING,peer.subject_id,stage=stage,related=closure.validation_parent.subject_id,predicate="ST_IsEmpty(ST_Difference(peer,region))",expected="true",actual="false",raw_predicate_result="false",difference_dimension=None if r[3] is None else int(r[3]),area_km2=area,area_ratio=ratio,residual_class=decision.residual_class.value,bbox=str(r[4] or ""),point=str(r[5] or ""),repair_eligibility=RepairEligibility.CONTEXT_ONLY.value))
        return tuple(out)

    def _repair_eligible(self, closure, assessment):
        blocking=assessment.blocking_findings
        if not blocking or self.repair_mode is RepairMode.DISABLED:return False
        if any(item.rule_code not in _REPAIRABLE_CODES for item in blocking):return False
        # R3 deliberately removes R2's ability to auto-construct material
        # "governed structural" geometry.  That mode is reserved for future
        # externally approved successors; this engine only constructs micro repairs.
        return all(item.repair_eligibility==RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE.value for item in blocking)

    def _successor(self, original: GeometryCandidate, ewkb_hex: str, geometry_type_code: str) -> GeometryCandidate:
        checksum=sha256(bytes.fromhex(ewkb_hex)).hexdigest()
        source_id=_stable_id("spatial-successor:nngla:",original.source_candidate_id,original.subject_id,REPAIR_POLICY_ID,checksum)
        return GeometryCandidate(
            root_place_id=original.root_place_id,subject_type=original.subject_type,subject_id=original.subject_id,
            geometry_role=original.geometry_role,source_candidate_id=source_id,geometry_type_code=geometry_type_code,
            encoding=GeometryEncoding.EWKB_HEX,payload=ewkb_hex,checksum_sha256=checksum,
            reservation_key=f"p006.7.11.15.5:successor:{original.subject_id}:{checksum[:24]}",
            source_dataset_id=original.source_dataset_id,source_dataset_version=original.source_dataset_version,
            source_path_reference=f"derived:{REPAIR_POLICY_ID}:{original.source_path_reference}",
            predecessor_source_candidate_id=original.source_candidate_id,repair_policy_id=REPAIR_POLICY_ID,
        )

    def _repair_selected_fabric(self, closure: CityClosure, originals: tuple[GeometryCandidate,...]) -> tuple[GeometryCandidate,...]:
        by_key={(item.subject_id,item.geometry_role):item for item in originals}
        city=by_key[(closure.admin_root.subject_id,GeometryRole.ADMINISTRATIVE_BOUNDARY)]
        children=tuple(by_key[(item.subject_id,GeometryRole.ADMINISTRATIVE_BOUNDARY)] for item in closure.exhaustive_children)
        result=reconcile_city_partition(self.connection,closure,city,children,self._successor)
        replacements={(result.city.subject_id,result.city.geometry_role):result.city}
        replacements.update({(item.subject_id,item.geometry_role):item for item in result.children})
        return tuple(replacements.get((item.subject_id,item.geometry_role),item) for item in originals)


class PassThroughTopologyEngine:
    """Database-free test adapter; live execution must use PostGISSpatialTopologyEngine."""
    repair_mode="TEST_PASSTHROUGH"
    def assess(self, closure: CityClosure) -> TopologyAssessment:
        return TopologyAssessment(closure.root.place_id,closure.desired_candidates,())


__all__=[
    "TOPOLOGY_POLICY_ID","REPAIR_POLICY_ID","DIAGNOSTIC_EQUAL_AREA_SRID",
    "MAX_AUTOMATIC_RESIDUAL_KM2","MAX_AUTOMATIC_RESIDUAL_RATIO",
    "PostGISSpatialTopologyEngine","PassThroughTopologyEngine",
]
