BEGIN;

-- P006.7.11.15.9.2 - CITY_DISTRICT Spatial Truth & Publication
-- Append-only successor to sequence 26 MUNICIPALITY publication.
-- Exact partition topology is authoritative: ST_Equals is required for PASS.
-- No tolerance/area epsilon may manufacture COMPLETE from a non-equal partition.

CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_city_district_geometry_record (
    district_geometry_id text PRIMARY KEY CHECK (district_geometry_id LIKE 'city-district-geometry:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_city_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_city_geometry_id text NOT NULL REFERENCES geography.nngla_city_geometry_record(city_geometry_id) ON DELETE RESTRICT,
    parent_city_geometry_sha256 text NOT NULL CHECK (parent_city_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    canonical_name text NOT NULL CHECK (btrim(canonical_name) <> ''),
    source_record_id text NOT NULL CHECK (btrim(source_record_id) <> ''),
    parent_source_record_id text NOT NULL CHECK (btrim(parent_source_record_id) <> ''),
    source_dataset_id text NOT NULL CHECK (btrim(source_dataset_id) <> ''),
    source_dataset_version text NOT NULL CHECK (btrim(source_dataset_version) <> ''),
    source_path_reference text NOT NULL CHECK (btrim(source_path_reference) <> ''),
    source_dataset_sha256 text NOT NULL CHECK (source_dataset_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    realization_method text NOT NULL CHECK (realization_method IN ('SOURCE_REUSE','CITY_PARTITION_NORMALIZATION')),
    realization_version integer NOT NULL DEFAULT 1 CHECK (realization_version=1),
    geometry_type_code text NOT NULL CHECK (geometry_type_code IN ('POLYGON','MULTIPOLYGON')),
    crs_code text NOT NULL CHECK (crs_code='NG-CRS-EPSG4326'),
    geometry geometry(Geometry,4326) NOT NULL,
    area_m2 double precision NOT NULL CHECK (area_m2 > 0),
    area_km2 double precision NOT NULL CHECK (area_km2 > 0),
    perimeter_m double precision NOT NULL CHECK (perimeter_m > 0),
    perimeter_km double precision NOT NULL CHECK (perimeter_km > 0),
    label_point geometry(Point,4326) NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    qualification_status text NOT NULL CHECK (qualification_status IN ('QUALIFIED','SUPERSEDED','WITHDRAWN')),
    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (district_geometry_id,administrative_area_id),
    CHECK (administrative_area_id <> parent_city_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (NOT ST_IsEmpty(geometry) AND ST_IsValid(geometry) AND ST_SRID(geometry)=4326),
    CHECK (ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')),
    CHECK (geometry_type_code = CASE WHEN ST_GeometryType(geometry)='ST_Polygon' THEN 'POLYGON' ELSE 'MULTIPOLYGON' END),
    CHECK (NOT ST_IsEmpty(label_point) AND ST_IsValid(label_point) AND ST_SRID(label_point)=4326 AND ST_CoveredBy(label_point,geometry))
);

CREATE UNIQUE INDEX ux_nngla_city_district_geometry_current ON geography.nngla_city_district_geometry_record(administrative_area_id)
WHERE effective_to IS NULL AND qualification_status='QUALIFIED';
CREATE UNIQUE INDEX ux_nngla_city_district_geometry_sha256 ON geography.nngla_city_district_geometry_record(geometry_sha256);
CREATE INDEX ix_nngla_city_district_geometry_parent ON geography.nngla_city_district_geometry_record(parent_city_id,parent_city_geometry_id);
CREATE INDEX ix_nngla_city_district_geometry_source ON geography.nngla_city_district_geometry_record(source_dataset_id,source_record_id);
CREATE INDEX ix_nngla_city_district_geometry_gist ON geography.nngla_city_district_geometry_record USING gist(geometry);
CREATE INDEX ix_nngla_city_district_label_point_gist ON geography.nngla_city_district_geometry_record USING gist(label_point);

CREATE TABLE geography.nngla_city_district_partition_qualification (
    partition_qualification_id text PRIMARY KEY CHECK (partition_qualification_id LIKE 'city-district-partition:nngla:%'),
    parent_city_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_city_geometry_id text NOT NULL REFERENCES geography.nngla_city_geometry_record(city_geometry_id) ON DELETE RESTRICT,
    parent_city_geometry_sha256 text NOT NULL CHECK (parent_city_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    expected_district_count integer NOT NULL CHECK (expected_district_count > 0),
    observed_district_count integer NOT NULL CHECK (observed_district_count >= 0),
    district_geometry_set_sha256 text NOT NULL CHECK (district_geometry_set_sha256 ~ '^[0-9a-f]{64}$'),
    district_member_set jsonb NOT NULL CHECK (jsonb_typeof(district_member_set)='array'),
    all_valid boolean NOT NULL,
    all_non_empty boolean NOT NULL,
    all_polygonal boolean NOT NULL,
    all_covered_by_city boolean NOT NULL,
    sibling_positive_overlap_m2 double precision NOT NULL CHECK (sibling_positive_overlap_m2 >= 0),
    union_equals_city boolean NOT NULL,
    union_area_m2 double precision NOT NULL CHECK (union_area_m2 >= 0),
    city_area_m2 double precision NOT NULL CHECK (city_area_m2 > 0),
    symmetric_difference_m2 double precision NOT NULL CHECK (symmetric_difference_m2 >= 0),
    partition_status text NOT NULL CHECK (partition_status IN ('COMPLETE','INCOMPLETE','REJECTED')),
    qualification_policy_version integer NOT NULL DEFAULT 1 CHECK (qualification_policy_version=1),
    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (partition_status <> 'COMPLETE' OR (
        observed_district_count=expected_district_count
        AND jsonb_array_length(district_member_set)=expected_district_count
        AND all_valid AND all_non_empty AND all_polygonal AND all_covered_by_city
        AND sibling_positive_overlap_m2=0 AND union_equals_city
    ))
);
CREATE UNIQUE INDEX ux_nngla_city_district_partition_current ON geography.nngla_city_district_partition_qualification(parent_city_id) WHERE effective_to IS NULL;
CREATE INDEX ix_nngla_city_district_partition_parent ON geography.nngla_city_district_partition_qualification(parent_city_id,parent_city_geometry_id);

CREATE TABLE geography.nngla_city_district_publication (
    publication_id text PRIMARY KEY CHECK (publication_id LIKE 'city-district-publication:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    district_geometry_id text NOT NULL,
    partition_qualification_id text NOT NULL REFERENCES geography.nngla_city_district_partition_qualification(partition_qualification_id) ON DELETE RESTRICT,
    publication_status text NOT NULL CHECK (publication_status IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publication_status <> 'PUBLISHED' OR published_at IS NOT NULL),
    FOREIGN KEY (district_geometry_id,administrative_area_id) REFERENCES geography.nngla_city_district_geometry_record(district_geometry_id,administrative_area_id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX ux_nngla_city_district_publication_current ON geography.nngla_city_district_publication(administrative_area_id) WHERE publication_status='PUBLISHED';
CREATE INDEX ix_nngla_city_district_publication_geometry ON geography.nngla_city_district_publication(district_geometry_id,publication_status);
CREATE INDEX ix_nngla_city_district_publication_partition ON geography.nngla_city_district_publication(partition_qualification_id);

-- Exact topology proof recomputation. ST_Equals, not area tolerance, is the PASS predicate.
CREATE VIEW geography.nngla_city_district_partition_exact_read_v1 AS
WITH current_district AS (
  SELECT * FROM geography.nngla_city_district_geometry_record
  WHERE effective_to IS NULL AND qualification_status='QUALIFIED'
), grouped AS (
  SELECT parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256,
         count(*)::integer AS observed_count,
         ST_UnaryUnion(ST_Collect(geometry)) AS district_union,
         bool_and(ST_IsValid(geometry)) AS all_valid,
         bool_and(NOT ST_IsEmpty(geometry)) AS all_non_empty,
         bool_and(ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')) AS all_polygonal
  FROM current_district GROUP BY parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256
)
SELECT g.parent_city_id,g.parent_city_geometry_id,g.parent_city_geometry_sha256,g.observed_count,
       g.all_valid,g.all_non_empty,g.all_polygonal,
       ST_Equals(g.district_union,c.geometry) AS union_equals_city,
       ST_Area(g.district_union::geography) AS union_area_m2,
       ST_Area(c.geometry::geography) AS city_area_m2,
       ST_Area(ST_SymDifference(g.district_union,c.geometry)::geography) AS symmetric_difference_m2
FROM grouped g
JOIN geography.nngla_city_geometry_record c
  ON c.city_geometry_id=g.parent_city_geometry_id
 AND c.administrative_area_id=g.parent_city_id
 AND c.geometry_sha256=g.parent_city_geometry_sha256
 AND c.effective_to IS NULL AND c.qualification_status='QUALIFIED';

CREATE VIEW geography.nngla_city_district_public_read_v1 AS
SELECT a.administrative_area_id AS district_id,g.parent_city_id,a.region_code,a.canonical_name,a.administrative_type_code,
       g.district_geometry_id,g.parent_city_geometry_id,g.parent_city_geometry_sha256,
       g.source_record_id,g.parent_source_record_id,g.source_dataset_id,g.source_dataset_version,g.source_path_reference,
       g.source_dataset_sha256,g.source_geometry_sha256,g.realization_method,g.realization_version,g.geometry_type_code,g.crs_code,
       g.area_m2,g.area_km2,g.perimeter_m,g.perimeter_km,ST_Y(g.label_point) AS label_latitude,ST_X(g.label_point) AS label_longitude,
       g.geometry,g.geometry_sha256,g.qualification_status,q.partition_qualification_id,q.partition_status,
       p.publication_id,p.publication_status,p.published_at
FROM geography.nngla_administrative_area a
JOIN geography.nngla_city_district_geometry_record g ON g.administrative_area_id=a.administrative_area_id AND g.effective_to IS NULL AND g.qualification_status='QUALIFIED'
JOIN geography.nngla_city_public_read_v1 c ON c.city_id=g.parent_city_id AND c.city_geometry_id=g.parent_city_geometry_id AND c.geometry_sha256=g.parent_city_geometry_sha256
JOIN geography.nngla_city_district_partition_qualification q ON q.parent_city_id=g.parent_city_id AND q.parent_city_geometry_id=g.parent_city_geometry_id AND q.parent_city_geometry_sha256=g.parent_city_geometry_sha256 AND q.effective_to IS NULL AND q.partition_status='COMPLETE'
JOIN geography.nngla_city_district_partition_exact_read_v1 x ON x.parent_city_id=q.parent_city_id AND x.parent_city_geometry_id=q.parent_city_geometry_id AND x.parent_city_geometry_sha256=q.parent_city_geometry_sha256 AND x.union_equals_city
JOIN geography.nngla_city_district_publication p ON p.administrative_area_id=a.administrative_area_id AND p.district_geometry_id=g.district_geometry_id AND p.partition_qualification_id=q.partition_qualification_id AND p.publication_status='PUBLISHED'
WHERE a.administrative_type_code IN ('DISTRICT','CITY_DISTRICT')
  AND g.canonical_name=a.canonical_name
  AND ST_CoveredBy(g.geometry,c.geometry)
  AND ST_CoveredBy(g.label_point,g.geometry)
  AND EXISTS (SELECT 1 FROM jsonb_array_elements(q.district_member_set) m(value) WHERE m.value->>'districtId'=a.administrative_area_id AND m.value->>'geometryId'=g.district_geometry_id AND m.value->>'geometrySha256'=g.geometry_sha256)
  AND NOT EXISTS (
      SELECT 1 FROM jsonb_array_elements(q.district_member_set) m(value)
      LEFT JOIN geography.nngla_city_district_geometry_record mg
        ON mg.administrative_area_id=m.value->>'districtId' AND mg.district_geometry_id=m.value->>'geometryId' AND mg.geometry_sha256=m.value->>'geometrySha256'
       AND mg.parent_city_id=q.parent_city_id AND mg.parent_city_geometry_id=q.parent_city_geometry_id
       AND mg.effective_to IS NULL AND mg.qualification_status='QUALIFIED'
      WHERE mg.district_geometry_id IS NULL
  );

COMMIT;
