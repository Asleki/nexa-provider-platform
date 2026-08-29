BEGIN;

-- NNGLA REGION Spatial Foundation
--
-- Purpose:
--   Provide a REGION-only geometry, measurement, publication and public-read
--   path for NoveGeo's eight REGION administrative identities.
--
-- Scope:
--   REGION only.
--
-- Deliberately independent from:
--   nngla_city_feature_qualification
--   nngla_administrative_geometry_adoption_decision
--   nngla_administrative_geometry_assignment
--   nngla_city_authority_receipt
--
-- Existing administrative identities remain authoritative:
--   geography.nngla_administrative_area

CREATE SCHEMA IF NOT EXISTS geography;


-- =====================================================================
-- 1. REGION GEOMETRY RECORD
-- =====================================================================

CREATE TABLE geography.nngla_region_geometry_record (
    region_geometry_id text PRIMARY KEY
        CHECK (
            region_geometry_id LIKE 'region-geometry:nngla:%'
        ),

    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,

    source_record_id text NOT NULL,

    canonical_name text NOT NULL,

    source_dataset_id text NOT NULL,

    source_dataset_version text NOT NULL,

    source_path_reference text NOT NULL,

    source_dataset_sha256 text NOT NULL
        CHECK (
            source_dataset_sha256 ~ '^[0-9a-f]{64}$'
        ),

    geometry_type_code text NOT NULL
        CHECK (
            geometry_type_code IN ('POLYGON', 'MULTIPOLYGON')
        ),

    crs_code text NOT NULL
        CHECK (
            crs_code = 'NG-CRS-EPSG4326'
        ),

    geometry geometry(Geometry,4326) NOT NULL,

    area_m2 double precision NOT NULL
        CHECK (area_m2 > 0),

    area_km2 double precision NOT NULL
        CHECK (area_km2 > 0),

    perimeter_m double precision NOT NULL
        CHECK (perimeter_m > 0),

    perimeter_km double precision NOT NULL
        CHECK (perimeter_km > 0),

    label_point geometry(Point,4326) NOT NULL,

    geometry_sha256 text NOT NULL
        CHECK (
            geometry_sha256 ~ '^[0-9a-f]{64}$'
        ),

    qualification_status text NOT NULL
        CHECK (
            qualification_status IN (
                'QUALIFIED',
                'SUPERSEDED',
                'WITHDRAWN'
            )
        ),

    effective_from date NOT NULL,

    effective_to date,

    created_at timestamptz NOT NULL DEFAULT now(),

    CHECK (
        effective_to IS NULL
        OR effective_to >= effective_from
    ),

    CHECK (
        NOT ST_IsEmpty(geometry)
        AND ST_IsValid(geometry)
        AND ST_SRID(geometry) = 4326
    ),

    CHECK (
        NOT ST_IsEmpty(label_point)
        AND ST_IsValid(label_point)
        AND ST_SRID(label_point) = 4326
    ),

    CHECK (
        ST_GeometryType(geometry)
        IN ('ST_Polygon', 'ST_MultiPolygon')
    ),

    CHECK (
        geometry_type_code =
        CASE
            WHEN ST_GeometryType(geometry) = 'ST_Polygon'
                THEN 'POLYGON'
            WHEN ST_GeometryType(geometry) = 'ST_MultiPolygon'
                THEN 'MULTIPOLYGON'
        END
    ),

    CHECK (
        ST_CoveredBy(label_point, geometry)
    )
);


CREATE UNIQUE INDEX ux_nngla_region_geometry_current
ON geography.nngla_region_geometry_record(administrative_area_id)
WHERE
    effective_to IS NULL
    AND qualification_status = 'QUALIFIED';


CREATE UNIQUE INDEX ux_nngla_region_geometry_sha256
ON geography.nngla_region_geometry_record(geometry_sha256);


CREATE INDEX ix_nngla_region_geometry_source
ON geography.nngla_region_geometry_record(
    source_dataset_id,
    source_record_id
);


CREATE INDEX ix_nngla_region_geometry_gist
ON geography.nngla_region_geometry_record
USING gist(geometry);


CREATE INDEX ix_nngla_region_label_point_gist
ON geography.nngla_region_geometry_record
USING gist(label_point);



-- =====================================================================
-- 2. REGION PUBLICATION
-- =====================================================================

CREATE TABLE geography.nngla_region_publication (
    publication_id text PRIMARY KEY
        CHECK (
            publication_id LIKE 'region-publication:nngla:%'
        ),

    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,

    region_geometry_id text NOT NULL
        REFERENCES geography.nngla_region_geometry_record(region_geometry_id)
        ON DELETE RESTRICT,

    publication_status text NOT NULL
        CHECK (
            publication_status IN (
                'PUBLISHED',
                'WITHDRAWN',
                'SUPERSEDED'
            )
        ),

    published_at timestamptz,

    created_at timestamptz NOT NULL DEFAULT now(),

    CHECK (
        publication_status <> 'PUBLISHED'
        OR published_at IS NOT NULL
    )
);


CREATE UNIQUE INDEX ux_nngla_region_publication_current
ON geography.nngla_region_publication(administrative_area_id)
WHERE publication_status = 'PUBLISHED';


CREATE INDEX ix_nngla_region_publication_geometry
ON geography.nngla_region_publication(
    region_geometry_id,
    publication_status
);



-- =====================================================================
-- 3. PUBLIC REGION READ MODEL
-- =====================================================================

CREATE VIEW geography.nngla_region_public_read_v1 AS

SELECT
    a.administrative_area_id AS region_id,

    a.region_code,

    a.canonical_name,

    a.administrative_type_code,

    g.region_geometry_id,

    g.source_record_id,

    g.source_dataset_id,

    g.source_dataset_version,

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

FROM geography.nngla_administrative_area AS a

JOIN geography.nngla_region_geometry_record AS g
  ON g.administrative_area_id = a.administrative_area_id
 AND g.effective_to IS NULL
 AND g.qualification_status = 'QUALIFIED'

JOIN geography.nngla_region_publication AS p
  ON p.administrative_area_id = a.administrative_area_id
 AND p.region_geometry_id = g.region_geometry_id
 AND p.publication_status = 'PUBLISHED'

WHERE
    a.administrative_type_code = 'REGION';


COMMIT;
