"""Shared-fabric successor construction for P006.7.11.15.5 R3.

Only ambiguous defect cells are reassigned.  Stable source district territory is
preserved; the final city is first normalized against its parent and Boundary v2,
then a canonical-seed Voronoi partition allocates gap/overlap cells without using
administrative-ID order as a territorial ownership rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import CityClosure, GeometryCandidate, GeometryEncoding


class PartitionReconciliationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PartitionReconciliationResult:
    city: GeometryCandidate
    children: tuple[GeometryCandidate, ...]
    defect_area_km2: float


def _candidate_values(candidates):
    rows = tuple(candidates)
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


def reconcile_city_partition(
    connection,
    closure: CityClosure,
    city: GeometryCandidate,
    children: tuple[GeometryCandidate, ...],
    successor_factory: Callable[[GeometryCandidate, str, str], GeometryCandidate],
) -> PartitionReconciliationResult:
    if len(children) != len(closure.exhaustive_child_seeds):
        raise PartitionReconciliationError("child/seed cardinality mismatch")
    by_seed = {seed.subject_id: seed for seed in closure.exhaustive_child_seeds}
    if set(by_seed) != {child.subject_id for child in children}:
        raise PartitionReconciliationError("child/seed identity mismatch")

    candidates = (city, closure.validation_parent) + tuple(children)
    cte, params = _candidate_values(candidates)
    seed_values = ",".join(["(%s,%s,%s)"] * len(children))
    seed_params: list[object] = []
    for child in children:
        seed = by_seed[child.subject_id]
        seed_params.extend((seed.subject_id, float(seed.longitude), float(seed.latitude)))
    child_ids = tuple(child.subject_id for child in children)
    child_placeholders = ",".join(["%s"] * len(child_ids))

    # The R3 final partition is constructed in one PostGIS statement so every
    # child sees the same final city and the same defect domain.  This eliminates
    # the R2 sequential child-order ownership side effect.
    sql = f"""
    /* P006.7.11.15.5 R3_FINAL_PARTITION */
    WITH {cte},
    sovereign AS (
      SELECT geometry
      FROM geography.world_boundary_version
      WHERE boundary_id='boundary:novegeo:sovereign'
        AND boundary_version=2
        AND lifecycle_status='active'
      LIMIT 1
    ),
    source_city AS (
      SELECT geometry FROM geom WHERE subject_id=%s
    ),
    validation_parent AS (
      SELECT geometry FROM geom WHERE subject_id=%s
    ),
    final_city AS (
      SELECT ST_CollectionExtract(
               ST_MakeValid(ST_Intersection(ST_Intersection(c.geometry,p.geometry),s.geometry)),3
             ) AS geometry
      FROM source_city c CROSS JOIN validation_parent p CROSS JOIN sovereign s
    ),
    source_children AS (
      SELECT subject_id,geometry FROM geom WHERE subject_id IN ({child_placeholders})
    ),
    clipped AS (
      SELECT subject_id,
             ST_CollectionExtract(ST_MakeValid(ST_Intersection(c.geometry,f.geometry)),3) AS geometry
      FROM source_children c CROSS JOIN final_city f
    ),
    pair_intersections AS (
      SELECT a.subject_id AS a_id,b.subject_id AS b_id,
             ST_Intersection(a.geometry,b.geometry) AS geometry
      FROM clipped a JOIN clipped b ON a.subject_id < b.subject_id
    ),
    positive_overlaps AS (
      SELECT a_id,b_id,ST_CollectionExtract(ST_MakeValid(geometry),3) AS geometry
      FROM pair_intersections
      WHERE NOT ST_IsEmpty(geometry) AND ST_Dimension(geometry)=2
    ),
    overlap_domain AS (
      SELECT COALESCE(
               ST_UnaryUnion(ST_Collect(geometry)),
               ST_GeomFromText('POLYGON EMPTY',4326)
             ) AS geometry
      FROM positive_overlaps
    ),
    stable AS (
      SELECT c.subject_id,
             ST_CollectionExtract(ST_MakeValid(ST_Difference(c.geometry,o.geometry)),3) AS geometry
      FROM clipped c CROSS JOIN overlap_domain o
    ),
    stable_union AS (
      SELECT COALESCE(
               ST_UnaryUnion(ST_Collect(geometry)),
               ST_GeomFromText('POLYGON EMPTY',4326)
             ) AS geometry
      FROM stable
    ),
    defect AS (
      SELECT ST_CollectionExtract(ST_MakeValid(ST_Difference(f.geometry,u.geometry)),3) AS geometry
      FROM final_city f CROSS JOIN stable_union u
    ),
    seed_raw(subject_id,longitude,latitude) AS (VALUES {seed_values}),
    seeds AS (
      SELECT subject_id,ST_SetSRID(ST_MakePoint(longitude,latitude),4326) AS geometry
      FROM seed_raw
    ),
    seed_collection AS (
      SELECT ST_Collect(geometry) AS geometry FROM seeds
    ),
    voronoi_dump AS (
      SELECT row_number() OVER () AS cell_id,d.geom AS geometry
      FROM seed_collection sc CROSS JOIN final_city f
      CROSS JOIN LATERAL ST_Dump(
        ST_VoronoiPolygons(sc.geometry,0.0,ST_Envelope(f.geometry))
      ) AS d
    ),
    cell_matches AS (
      SELECT v.cell_id,s.subject_id,v.geometry
      FROM voronoi_dump v JOIN seeds s ON ST_Covers(v.geometry,s.geometry)
    ),
    seed_cell_counts AS (
      SELECT s.subject_id,COUNT(m.cell_id) AS cell_count
      FROM seeds s LEFT JOIN cell_matches m ON m.subject_id=s.subject_id
      GROUP BY s.subject_id
    ),
    seed_cells AS (
      SELECT subject_id,ST_UnaryUnion(ST_Collect(geometry)) AS geometry
      FROM cell_matches GROUP BY subject_id
    ),
    allocated AS (
      SELECT s.subject_id,
             ST_CollectionExtract(ST_MakeValid(ST_Intersection(d.geometry,s.geometry)),3) AS geometry
      FROM seed_cells s CROSS JOIN defect d
    ),
    final_children AS (
      SELECT st.subject_id,
             ST_CollectionExtract(
               ST_MakeValid(
                 ST_UnaryUnion(
                   ST_Collect(st.geometry,COALESCE(a.geometry,ST_GeomFromText('POLYGON EMPTY',4326)))
                 )
               ),3
             ) AS geometry
      FROM stable st LEFT JOIN allocated a ON a.subject_id=st.subject_id
    ),
    diagnostics AS (
      SELECT
        (SELECT COUNT(*) FROM seeds) AS seed_count,
        (SELECT COUNT(*) FROM seed_cell_counts WHERE cell_count=1) AS mapped_seed_count,
        (SELECT COUNT(*) FROM seed_cell_counts WHERE cell_count<>1) AS ambiguous_seed_count,
        ST_Area(ST_Transform((SELECT geometry FROM defect),6933))/1000000.0 AS defect_area_km2
    )
    SELECT '__CITY__' AS subject_id,
           encode(ST_AsEWKB(f.geometry),'hex') AS ewkb_hex,
           upper(replace(ST_GeometryType(f.geometry),'ST_','')) AS geometry_type,
           d.seed_count,d.mapped_seed_count,d.ambiguous_seed_count,d.defect_area_km2
    FROM final_city f CROSS JOIN diagnostics d
    UNION ALL
    SELECT c.subject_id,
           encode(ST_AsEWKB(c.geometry),'hex'),
           upper(replace(ST_GeometryType(c.geometry),'ST_','')),
           d.seed_count,d.mapped_seed_count,d.ambiguous_seed_count,d.defect_area_km2
    FROM final_children c CROSS JOIN diagnostics d
    ORDER BY subject_id
    """
    values = tuple(params) + (city.subject_id, closure.validation_parent.subject_id) + child_ids + tuple(seed_params)
    with connection.cursor() as cur:
        cur.execute(sql, values)
        rows = cur.fetchall()
    if not rows:
        raise PartitionReconciliationError("PostGIS returned no R3 successor fabric")

    city_row = next((row for row in rows if str(row[0]) == "__CITY__"), None)
    if city_row is None:
        raise PartitionReconciliationError("R3 successor city is missing")
    seed_count = int(city_row[3] or 0)
    mapped_seed_count = int(city_row[4] or 0)
    ambiguous_seed_count = int(city_row[5] or 0)
    if seed_count != len(children) or mapped_seed_count != len(children) or ambiguous_seed_count:
        raise PartitionReconciliationError(
            f"canonical defect-cell owner mapping is ambiguous: seeds={seed_count};mapped={mapped_seed_count};ambiguous={ambiguous_seed_count}"
        )

    child_rows = {str(row[0]): row for row in rows if str(row[0]) != "__CITY__"}
    if set(child_rows) != set(child_ids):
        raise PartitionReconciliationError("R3 successor district set is incomplete")
    if not city_row[1] or str(city_row[2]) not in {"POLYGON", "MULTIPOLYGON"}:
        raise PartitionReconciliationError("R3 successor city is not non-empty polygonal geometry")

    successor_city = successor_factory(city, str(city_row[1]), str(city_row[2]))
    successor_children = []
    by_original = {item.subject_id: item for item in children}
    for subject_id in child_ids:
        row = child_rows[subject_id]
        if not row[1] or str(row[2]) not in {"POLYGON", "MULTIPOLYGON"}:
            raise PartitionReconciliationError(f"R3 successor child is not polygonal: {subject_id}")
        successor_children.append(successor_factory(by_original[subject_id], str(row[1]), str(row[2])))

    return PartitionReconciliationResult(
        city=successor_city,
        children=tuple(successor_children),
        defect_area_km2=float(city_row[6] or 0.0),
    )


__all__ = [
    "PartitionReconciliationError",
    "PartitionReconciliationResult",
    "reconcile_city_partition",
]
