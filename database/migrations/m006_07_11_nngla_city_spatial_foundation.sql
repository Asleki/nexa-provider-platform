BEGIN;

-- P006.7.11.15.7.1 — NNGLA Governed CITY Spatial Authority & Publication Foundation
--
-- Purpose:
--   Establish a new CITY-specific PostgreSQL spatial authority following the
--   successful P006.7.11.15.6 REGION architecture.  Legacy Bundle19B geometry
--   may be provenance/realization input only; the final stored geometry in
--   geography.nngla_city_geometry_record is authoritative for this path.
--
-- Deliberately independent from historical Delivery 1–3 CITY contracts:
--   geography.nngla_city_feature_qualification
--   geography.nngla_administrative_geometry_adoption_decision
--   geography.nngla_administrative_geometry_assignment
--   geography.nngla_city_authority_receipt
-- and from shared-face recovery / candidate reconstruction workflows.
--
-- Scope:
--   CITY only.  No MUNICIPALITY, DISTRICT, TOWN, VILLAGE, ROAD, ADDRESS,
--   PARCEL or complete REGION-partition publication gate is introduced here.

CREATE SCHEMA IF NOT EXISTS geography;


-- =====================================================================
-- 1. AUTHORITATIVE CITY GEOMETRY RECORD
-- =====================================================================

CREATE TABLE geography.nngla_city_geometry_record (
    city_geometry_id text PRIMARY KEY
        CHECK (city_geometry_id LIKE 'city-geometry:nngla:%'),

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

    canonical_name text NOT NULL
        CHECK (btrim(canonical_name) <> ''),

    source_record_id text NOT NULL
        CHECK (btrim(source_record_id) <> ''),

    source_dataset_id text NOT NULL
        CHECK (btrim(source_dataset_id) <> ''),

    source_dataset_version text NOT NULL
        CHECK (btrim(source_dataset_version) <> ''),

    source_path_reference text NOT NULL
        CHECK (btrim(source_path_reference) <> ''),

    source_dataset_sha256 text NOT NULL
        CHECK (source_dataset_sha256 ~ '^[0-9a-f]{64}$'),

    source_geometry_sha256 text NOT NULL
        CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),

    realization_method text NOT NULL
        CHECK (
            realization_method IN (
                'SOURCE_REUSE',
                'PARENT_CONTAINED_NORMALIZATION'
            )
        ),

    realization_version integer NOT NULL DEFAULT 1
        CHECK (realization_version >= 1),

    geometry_type_code text NOT NULL
        CHECK (geometry_type_code IN ('POLYGON', 'MULTIPOLYGON')),

    crs_code text NOT NULL
        CHECK (crs_code = 'NG-CRS-EPSG4326'),

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
        CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),

    UNIQUE (city_geometry_id, administrative_area_id),

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

    CHECK (administrative_area_id <> parent_region_id),

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
        ST_GeometryType(geometry)
        IN ('ST_Polygon', 'ST_MultiPolygon')
    ),

    CHECK (
        geometry_type_code = CASE
            WHEN ST_GeometryType(geometry) = 'ST_Polygon' THEN 'POLYGON'
            WHEN ST_GeometryType(geometry) = 'ST_MultiPolygon' THEN 'MULTIPOLYGON'
        END
    ),

    CHECK (
        NOT ST_IsEmpty(label_point)
        AND ST_IsValid(label_point)
        AND ST_SRID(label_point) = 4326
        AND ST_CoveredBy(label_point, geometry)
    )
);

CREATE UNIQUE INDEX ux_nngla_city_geometry_current
ON geography.nngla_city_geometry_record(administrative_area_id)
WHERE
    effective_to IS NULL
    AND qualification_status = 'QUALIFIED';

CREATE UNIQUE INDEX ux_nngla_city_geometry_sha256
ON geography.nngla_city_geometry_record(geometry_sha256);

CREATE INDEX ix_nngla_city_geometry_parent
ON geography.nngla_city_geometry_record(
    parent_region_id,
    parent_region_geometry_id
);

CREATE INDEX ix_nngla_city_geometry_source
ON geography.nngla_city_geometry_record(
    source_dataset_id,
    source_record_id
);

CREATE INDEX ix_nngla_city_geometry_gist
ON geography.nngla_city_geometry_record
USING gist(geometry);

CREATE INDEX ix_nngla_city_label_point_gist
ON geography.nngla_city_geometry_record
USING gist(label_point);


-- =====================================================================
-- 2. CITY PUBLICATION
-- =====================================================================

CREATE TABLE geography.nngla_city_publication (
    publication_id text PRIMARY KEY
        CHECK (publication_id LIKE 'city-publication:nngla:%'),

    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,

    city_geometry_id text NOT NULL,

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
    ),

    FOREIGN KEY (city_geometry_id, administrative_area_id)
        REFERENCES geography.nngla_city_geometry_record(
            city_geometry_id,
            administrative_area_id
        )
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX ux_nngla_city_publication_current
ON geography.nngla_city_publication(administrative_area_id)
WHERE publication_status = 'PUBLISHED';

CREATE INDEX ix_nngla_city_publication_geometry
ON geography.nngla_city_publication(
    city_geometry_id,
    publication_status
);


-- =====================================================================
-- 3. PUBLIC CITY READ MODEL
-- =====================================================================
--
-- This view is fail-closed.  A CITY is public only while:
--   * the administrative identity is classified CITY;
--   * the referenced parent identity is classified REGION;
--   * the CITY geometry is current + QUALIFIED;
--   * its exact parent REGION geometry is current + QUALIFIED;
--   * the stored parent REGION hash matches that exact parent geometry;
--   * the final CITY geometry is covered by that parent geometry;
--   * the publication is current + PUBLISHED.
--
-- It intentionally does not consult any Delivery 1–3 CITY qualification,
-- adoption, assignment or authority-receipt table.

CREATE VIEW geography.nngla_city_public_read_v1 AS
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

COMMIT;
