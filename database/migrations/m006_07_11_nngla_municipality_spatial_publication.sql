BEGIN;

-- P006.7.11.15.9.1 - MUNICIPALITY Spatial Truth & Publication
--
-- Bundle19B is identity/coordinate/topology/provenance evidence only.
-- Final geometry stored in this migration is the sole authority for this path.
-- REGION and CITY authority are immutable parents and are not modified.
-- Historical Delivery 1-3 publication/adoption tables are not consulted.

CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_municipality_geometry_record (
    municipality_geometry_id text PRIMARY KEY
        CHECK (municipality_geometry_id LIKE 'municipality-geometry:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    parent_region_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    parent_region_geometry_id text NOT NULL
        REFERENCES geography.nngla_region_geometry_record(region_geometry_id)
        ON DELETE RESTRICT,
    parent_region_geometry_sha256 text NOT NULL
        CHECK (parent_region_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    canonical_name text NOT NULL CHECK (btrim(canonical_name) <> ''),
    source_record_id text NOT NULL CHECK (btrim(source_record_id) <> ''),
    source_dataset_id text NOT NULL CHECK (btrim(source_dataset_id) <> ''),
    source_dataset_version text NOT NULL CHECK (btrim(source_dataset_version) <> ''),
    source_path_reference text NOT NULL CHECK (btrim(source_path_reference) <> ''),
    source_dataset_sha256 text NOT NULL
        CHECK (source_dataset_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL
        CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    realization_method text NOT NULL
        CHECK (
            realization_method IN (
                'SOURCE_REUSE',
                'REGION_CITY_CONTAINED_NORMALIZATION'
            )
        ),
    realization_version integer NOT NULL DEFAULT 1
        CHECK (realization_version = 1),
    geometry_type_code text NOT NULL
        CHECK (geometry_type_code IN ('POLYGON','MULTIPOLYGON')),
    crs_code text NOT NULL CHECK (crs_code='NG-CRS-EPSG4326'),
    geometry geometry(Geometry,4326) NOT NULL,
    area_m2 double precision NOT NULL CHECK (area_m2 > 0),
    area_km2 double precision NOT NULL CHECK (area_km2 > 0),
    perimeter_m double precision NOT NULL CHECK (perimeter_m > 0),
    perimeter_km double precision NOT NULL CHECK (perimeter_km > 0),
    label_point geometry(Point,4326) NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    qualification_status text NOT NULL
        CHECK (qualification_status IN ('QUALIFIED','SUPERSEDED','WITHDRAWN')),
    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (municipality_geometry_id,administrative_area_id),
    CHECK (administrative_area_id <> parent_region_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (
        NOT ST_IsEmpty(geometry)
        AND ST_IsValid(geometry)
        AND ST_SRID(geometry)=4326
    ),
    CHECK (ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')),
    CHECK (
        geometry_type_code = CASE
            WHEN ST_GeometryType(geometry)='ST_Polygon' THEN 'POLYGON'
            WHEN ST_GeometryType(geometry)='ST_MultiPolygon' THEN 'MULTIPOLYGON'
        END
    ),
    CHECK (
        NOT ST_IsEmpty(label_point)
        AND ST_IsValid(label_point)
        AND ST_SRID(label_point)=4326
        AND ST_CoveredBy(label_point,geometry)
    )
);

CREATE UNIQUE INDEX ux_nngla_municipality_geometry_current
ON geography.nngla_municipality_geometry_record(administrative_area_id)
WHERE effective_to IS NULL AND qualification_status='QUALIFIED';

CREATE UNIQUE INDEX ux_nngla_municipality_geometry_sha256
ON geography.nngla_municipality_geometry_record(geometry_sha256);

CREATE INDEX ix_nngla_municipality_geometry_parent
ON geography.nngla_municipality_geometry_record(
    parent_region_id,parent_region_geometry_id
);

CREATE INDEX ix_nngla_municipality_geometry_source
ON geography.nngla_municipality_geometry_record(
    source_dataset_id,source_record_id
);

CREATE INDEX ix_nngla_municipality_geometry_gist
ON geography.nngla_municipality_geometry_record USING gist(geometry);

CREATE INDEX ix_nngla_municipality_label_point_gist
ON geography.nngla_municipality_geometry_record USING gist(label_point);


CREATE TABLE geography.nngla_municipality_partition_qualification (
    partition_qualification_id text PRIMARY KEY
        CHECK (partition_qualification_id LIKE 'municipality-partition:nngla:%'),
    parent_region_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    parent_region_geometry_id text NOT NULL
        REFERENCES geography.nngla_region_geometry_record(region_geometry_id)
        ON DELETE RESTRICT,
    parent_region_geometry_sha256 text NOT NULL
        CHECK (parent_region_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    city_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    city_geometry_id text NOT NULL
        REFERENCES geography.nngla_city_geometry_record(city_geometry_id)
        ON DELETE RESTRICT,
    city_geometry_sha256 text NOT NULL
        CHECK (city_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    city_publication_id text NOT NULL
        REFERENCES geography.nngla_city_publication(publication_id)
        ON DELETE RESTRICT,
    expected_municipality_count integer NOT NULL DEFAULT 3
        CHECK (expected_municipality_count=3),
    observed_municipality_count integer NOT NULL
        CHECK (observed_municipality_count BETWEEN 0 AND 3),
    municipality_geometry_set_sha256 text NOT NULL
        CHECK (municipality_geometry_set_sha256 ~ '^[0-9a-f]{64}$'),
    municipality_member_set jsonb NOT NULL,
    all_valid boolean NOT NULL,
    all_non_empty boolean NOT NULL,
    all_polygonal boolean NOT NULL,
    all_covered_by_region boolean NOT NULL,
    city_covered_by_region boolean NOT NULL,
    municipality_sibling_positive_overlap_m2 double precision NOT NULL
        CHECK (municipality_sibling_positive_overlap_m2 >= 0),
    city_municipality_positive_overlap_m2 double precision NOT NULL
        CHECK (city_municipality_positive_overlap_m2 >= 0),
    union_equals_region boolean NOT NULL,
    union_area_m2 double precision NOT NULL CHECK (union_area_m2 >= 0),
    region_area_m2 double precision NOT NULL CHECK (region_area_m2 > 0),
    symmetric_difference_m2 double precision NOT NULL
        CHECK (symmetric_difference_m2 >= 0),
    partition_status text NOT NULL
        CHECK (partition_status IN ('COMPLETE','INCOMPLETE','REJECTED')),
    qualification_policy_version integer NOT NULL DEFAULT 1
        CHECK (qualification_policy_version=1),
    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (jsonb_typeof(municipality_member_set)='array'),
    CHECK (
        partition_status <> 'COMPLETE'
        OR (
            observed_municipality_count=3
            AND jsonb_array_length(municipality_member_set)=3
            AND all_valid
            AND all_non_empty
            AND all_polygonal
            AND all_covered_by_region
            AND city_covered_by_region
            AND municipality_sibling_positive_overlap_m2=0
            AND city_municipality_positive_overlap_m2=0
            AND union_equals_region
        )
    )
);

CREATE UNIQUE INDEX ux_nngla_municipality_partition_current
ON geography.nngla_municipality_partition_qualification(parent_region_id)
WHERE effective_to IS NULL;

CREATE INDEX ix_nngla_municipality_partition_parent
ON geography.nngla_municipality_partition_qualification(
    parent_region_id,parent_region_geometry_id
);

CREATE INDEX ix_nngla_municipality_partition_city
ON geography.nngla_municipality_partition_qualification(
    city_id,city_geometry_id
);


CREATE TABLE geography.nngla_municipality_publication (
    publication_id text PRIMARY KEY
        CHECK (publication_id LIKE 'municipality-publication:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    municipality_geometry_id text NOT NULL,
    partition_qualification_id text NOT NULL
        REFERENCES geography.nngla_municipality_partition_qualification(
            partition_qualification_id
        ) ON DELETE RESTRICT,
    publication_status text NOT NULL
        CHECK (publication_status IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publication_status <> 'PUBLISHED' OR published_at IS NOT NULL),
    FOREIGN KEY (municipality_geometry_id,administrative_area_id)
        REFERENCES geography.nngla_municipality_geometry_record(
            municipality_geometry_id,administrative_area_id
        ) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX ux_nngla_municipality_publication_current
ON geography.nngla_municipality_publication(administrative_area_id)
WHERE publication_status='PUBLISHED';

CREATE INDEX ix_nngla_municipality_publication_geometry
ON geography.nngla_municipality_publication(
    municipality_geometry_id,publication_status
);

CREATE INDEX ix_nngla_municipality_publication_partition
ON geography.nngla_municipality_publication(partition_qualification_id);


-- Fail-closed public model.  Publication survives only while the exact REGION
-- and CITY versions used by the COMPLETE proof remain current and published,
-- and every member in the qualified three-member set remains current.
CREATE VIEW geography.nngla_municipality_public_read_v1 AS
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
    q.partition_qualification_id,
    q.partition_status,
    q.city_id,
    q.city_geometry_id,
    q.city_geometry_sha256,
    q.city_publication_id,
    q.municipality_geometry_set_sha256,
    p.publication_id,
    p.publication_status,
    p.published_at
FROM geography.nngla_administrative_area AS a
JOIN geography.nngla_municipality_geometry_record AS g
  ON g.administrative_area_id=a.administrative_area_id
 AND g.effective_to IS NULL
 AND g.qualification_status='QUALIFIED'
JOIN geography.nngla_administrative_area AS region_admin
  ON region_admin.administrative_area_id=g.parent_region_id
 AND region_admin.administrative_type_code='REGION'
JOIN geography.nngla_region_geometry_record AS region_geometry
  ON region_geometry.region_geometry_id=g.parent_region_geometry_id
 AND region_geometry.administrative_area_id=g.parent_region_id
 AND region_geometry.geometry_sha256=g.parent_region_geometry_sha256
 AND region_geometry.effective_to IS NULL
 AND region_geometry.qualification_status='QUALIFIED'
JOIN geography.nngla_municipality_partition_qualification AS q
  ON q.parent_region_id=g.parent_region_id
 AND q.parent_region_geometry_id=g.parent_region_geometry_id
 AND q.parent_region_geometry_sha256=g.parent_region_geometry_sha256
 AND q.effective_to IS NULL
 AND q.partition_status='COMPLETE'
JOIN geography.nngla_city_public_read_v1 AS city_public
  ON city_public.city_id=q.city_id
 AND city_public.city_geometry_id=q.city_geometry_id
 AND city_public.geometry_sha256=q.city_geometry_sha256
 AND city_public.publication_id=q.city_publication_id
 AND city_public.parent_region_id=g.parent_region_id
JOIN geography.nngla_municipality_publication AS p
  ON p.administrative_area_id=a.administrative_area_id
 AND p.municipality_geometry_id=g.municipality_geometry_id
 AND p.partition_qualification_id=q.partition_qualification_id
 AND p.publication_status='PUBLISHED'
WHERE
    a.administrative_type_code='MUNICIPALITY'
    AND a.parent_source_record_id=region_admin.source_record_id
    AND a.region_code=region_admin.region_code
    AND g.canonical_name=a.canonical_name
    AND q.expected_municipality_count=3
    AND q.observed_municipality_count=3
    AND jsonb_array_length(q.municipality_member_set)=3
    AND ST_CoveredBy(g.geometry,region_geometry.geometry)
    AND ST_CoveredBy(g.label_point,g.geometry)
    AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements(q.municipality_member_set) AS member(value)
      WHERE member.value->>'municipalityId'=a.administrative_area_id
        AND member.value->>'geometryId'=g.municipality_geometry_id
        AND member.value->>'geometrySha256'=g.geometry_sha256
    )
    AND NOT EXISTS (
      SELECT 1
      FROM jsonb_array_elements(q.municipality_member_set) AS member(value)
      LEFT JOIN geography.nngla_municipality_geometry_record AS member_geometry
        ON member_geometry.administrative_area_id=member.value->>'municipalityId'
       AND member_geometry.municipality_geometry_id=member.value->>'geometryId'
       AND member_geometry.geometry_sha256=member.value->>'geometrySha256'
       AND member_geometry.parent_region_id=q.parent_region_id
       AND member_geometry.parent_region_geometry_id=q.parent_region_geometry_id
       AND member_geometry.parent_region_geometry_sha256=q.parent_region_geometry_sha256
       AND member_geometry.effective_to IS NULL
       AND member_geometry.qualification_status='QUALIFIED'
      WHERE member_geometry.municipality_geometry_id IS NULL
    )
    AND NOT EXISTS (
      SELECT 1
      FROM geography.nngla_municipality_geometry_record AS extra_geometry
      WHERE extra_geometry.parent_region_id=q.parent_region_id
        AND extra_geometry.effective_to IS NULL
        AND extra_geometry.qualification_status='QUALIFIED'
        AND NOT EXISTS (
          SELECT 1
          FROM jsonb_array_elements(q.municipality_member_set) AS member(value)
          WHERE member.value->>'municipalityId'=extra_geometry.administrative_area_id
            AND member.value->>'geometryId'=extra_geometry.municipality_geometry_id
            AND member.value->>'geometrySha256'=extra_geometry.geometry_sha256
        )
    );

COMMIT;
