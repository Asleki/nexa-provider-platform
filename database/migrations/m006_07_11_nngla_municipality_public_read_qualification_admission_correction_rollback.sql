BEGIN;

-- Restore the exact Sequence 29 MUNICIPALITY public-read predicates.

CREATE OR REPLACE VIEW geography.nngla_municipality_public_read_v2 AS
SELECT
    a.administrative_area_id AS municipality_id,
    g.parent_region_id,
    a.region_code,
    a.canonical_name,
    a.administrative_type_code,
    g.municipality_geometry_id,
    g.parent_region_geometry_id,
    g.parent_region_geometry_sha256,
    g.source_record_id,
    g.source_dataset_id,
    g.source_dataset_version,
    g.source_path_reference,
    g.source_dataset_sha256,
    g.source_geometry_sha256,
    g.realization_method,
    g.realization_version,
    g.geometry_type_code,
    g.crs_code,
    g.area_m2,
    g.area_km2,
    g.perimeter_m,
    g.perimeter_km,
    ST_Y(g.label_point) AS label_latitude,
    ST_X(g.label_point) AS label_longitude,
    g.geometry,
    g.geometry_sha256,
    g.qualification_status,
    fq.feature_qualification_id,
    pq.partition_qualification_id,
    COALESCE(fs.fabric_status,'PARTIAL') AS partition_status,
    COALESCE(fs.fabric_status,'PARTIAL') AS fabric_status,
    fq.city_id,
    fq.city_geometry_id,
    fq.city_geometry_sha256,
    c.publication_id AS city_publication_id,
    fp.publication_id,
    fp.publication_status,
    fp.published_at
FROM geography.nngla_administrative_area AS a
JOIN geography.nngla_municipality_geometry_record AS g
  ON g.administrative_area_id=a.administrative_area_id
 AND g.effective_to IS NULL
 AND g.qualification_status='QUALIFIED'
JOIN geography.nngla_region_public_read_v1 AS r
  ON r.region_id=g.parent_region_id
 AND r.region_geometry_id=g.parent_region_geometry_id
 AND r.geometry_sha256=g.parent_region_geometry_sha256
 AND r.administrative_type_code='REGION'
 AND r.qualification_status='QUALIFIED'
 AND r.publication_status='PUBLISHED'
JOIN geography.nngla_municipality_feature_qualification AS fq
  ON fq.administrative_area_id=a.administrative_area_id
 AND fq.municipality_geometry_id=g.municipality_geometry_id
 AND fq.geometry_sha256=g.geometry_sha256
 AND fq.source_geometry_sha256=g.source_geometry_sha256
 AND fq.parent_region_id=g.parent_region_id
 AND fq.parent_region_geometry_id=g.parent_region_geometry_id
 AND fq.parent_region_geometry_sha256=g.parent_region_geometry_sha256
 AND fq.qualification_status='QUALIFIED'
JOIN geography.nngla_city_public_read_v1 AS c
  ON c.city_id=fq.city_id
 AND c.city_geometry_id=fq.city_geometry_id
 AND c.geometry_sha256=fq.city_geometry_sha256
 AND c.parent_region_id=g.parent_region_id
 AND c.administrative_type_code='CITY'
 AND c.qualification_status='QUALIFIED'
 AND c.publication_status='PUBLISHED'
JOIN geography.nngla_municipality_feature_publication AS fp
  ON fp.administrative_area_id=a.administrative_area_id
 AND fp.municipality_geometry_id=g.municipality_geometry_id
 AND fp.feature_qualification_id=fq.feature_qualification_id
 AND fp.publication_status='PUBLISHED'
LEFT JOIN geography.nngla_municipality_fabric_status_read_v2 AS fs
  ON fs.parent_region_id=g.parent_region_id
 AND fs.parent_region_geometry_id=g.parent_region_geometry_id
 AND fs.parent_region_geometry_sha256=g.parent_region_geometry_sha256
 AND fs.city_id=fq.city_id
 AND fs.city_geometry_id=fq.city_geometry_id
 AND fs.city_geometry_sha256=fq.city_geometry_sha256
LEFT JOIN geography.nngla_municipality_partition_qualification AS pq
  ON pq.parent_region_id=g.parent_region_id
 AND pq.parent_region_geometry_id=g.parent_region_geometry_id
 AND pq.parent_region_geometry_sha256=g.parent_region_geometry_sha256
 AND pq.city_id=fq.city_id
 AND pq.city_geometry_id=fq.city_geometry_id
 AND pq.city_geometry_sha256=fq.city_geometry_sha256
 AND pq.effective_to IS NULL
WHERE a.administrative_type_code='MUNICIPALITY'
  AND a.parent_source_record_id=r.source_record_id
  AND a.region_code=r.region_code
  AND g.canonical_name=a.canonical_name
  AND ST_CoveredBy(g.geometry,r.geometry)
  AND ST_CoveredBy(g.label_point,g.geometry)
  AND ST_Area(
        ST_CollectionExtract(
          ST_Intersection(g.geometry,c.geometry),3
        )::geography
      )=0
  AND fq.identity_parentage_match
  AND fq.source_contract_match
  AND fq.is_valid
  AND fq.is_non_empty
  AND fq.is_polygonal
  AND fq.covered_by_parent_region
  AND fq.city_positive_overlap_m2=0
  AND fq.municipality_sibling_positive_overlap_m2=0
  AND EXISTS (
      SELECT 1
      FROM geography.nngla_execution_receipt AS er
      JOIN geography.nngla_execution_item AS ei
        ON ei.execution_id=er.execution_id
      WHERE er.plan_id='p006.7.11.15.9-seq29-municipality-feature-publication'
        AND er.plan_version=1
        AND er.runtime_mode='production'
        AND er.status IN ('APPLIED','REUSED')
        AND ei.canonical_id=a.administrative_area_id
        AND ei.publication_ready
        AND ei.detail->>'municipality_geometry_id'=g.municipality_geometry_id
        AND ei.detail->>'feature_qualification_id'=fq.feature_qualification_id
        AND ei.detail->>'publication_id'=fp.publication_id
        AND ei.detail->>'geometry_sha256'=g.geometry_sha256
  );


-- ---------------------------------------------------------------------------
-- TOWN public-read successor. Sequence 28 already has feature-level
-- qualification/publication; v2 only makes live MUNICIPALITY authority an
-- explicit continuing parent requirement.
-- ---------------------------------------------------------------------------

COMMIT;
