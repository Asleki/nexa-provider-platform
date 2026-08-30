BEGIN;

-- Restore the exact sequence-24 strict public-read predicate before removing
-- the additive containment-qualification objects.  No CITY/REGION authority
-- table or authoritative geometry row is dropped by this rollback.
CREATE OR REPLACE VIEW geography.nngla_city_public_read_v1 AS
SELECT
    city_admin.administrative_area_id AS city_id,
    g.parent_region_id,
    city_admin.region_code,
    city_admin.canonical_name,
    city_admin.administrative_type_code,
    g.city_geometry_id,
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
    p.publication_id,
    p.publication_status,
    p.published_at
FROM geography.nngla_administrative_area AS city_admin
JOIN geography.nngla_city_geometry_record AS g
  ON g.administrative_area_id = city_admin.administrative_area_id
 AND g.effective_to IS NULL
 AND g.qualification_status = 'QUALIFIED'
JOIN geography.nngla_administrative_area AS region_admin
  ON region_admin.administrative_area_id = g.parent_region_id
 AND region_admin.administrative_type_code = 'REGION'
JOIN geography.nngla_region_geometry_record AS region_geometry
  ON region_geometry.region_geometry_id = g.parent_region_geometry_id
 AND region_geometry.administrative_area_id = g.parent_region_id
 AND region_geometry.geometry_sha256 = g.parent_region_geometry_sha256
 AND region_geometry.effective_to IS NULL
 AND region_geometry.qualification_status = 'QUALIFIED'
JOIN geography.nngla_city_publication AS p
  ON p.administrative_area_id = city_admin.administrative_area_id
 AND p.city_geometry_id = g.city_geometry_id
 AND p.publication_status = 'PUBLISHED'
WHERE
    city_admin.administrative_type_code = 'CITY'
    AND g.canonical_name = city_admin.canonical_name
    AND city_admin.region_code = region_admin.region_code
    AND ST_CoveredBy(g.geometry, region_geometry.geometry)
    AND ST_CoveredBy(g.label_point, g.geometry)
    AND g.area_m2 > 0
    AND g.perimeter_m > 0;

DROP VIEW IF EXISTS geography.nngla_city_parent_containment_read_v1;
DROP TABLE IF EXISTS geography.nngla_city_parent_containment_qualification;

COMMIT;
