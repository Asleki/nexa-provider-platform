-- P006.7.11.7.19 additive NNGLA query/read-model contract.
-- Canonical tables remain write-authoritative. Query functions operate only on an
-- explicit visibility-governed projection and therefore cannot turn "canonical"
-- into "public" merely because a row exists.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_spatial_read_projection_v1 (
    projection_id text PRIMARY KEY CHECK (projection_id LIKE 'read:nngla:%'),
    subject_id text NOT NULL,
    record_family text NOT NULL,
    display_name text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    visibility text NOT NULL CHECK (visibility IN ('PUBLIC','INTERNAL','RESTRICTED')),
    publication_reference text,
    geometry_id text,
    geometry_version integer CHECK (geometry_version IS NULL OR geometry_version > 0),
    read_model_version integer NOT NULL CHECK (read_model_version > 0),
    projected_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(subject_id,runtime_mode,read_model_version),
    CHECK (visibility <> 'PUBLIC' OR publication_reference IS NOT NULL)
);

CREATE INDEX ix_nngla_spatial_read_projection_lookup
ON geography.nngla_spatial_read_projection_v1(runtime_mode,record_family,visibility,subject_id);

CREATE OR REPLACE VIEW geography.nngla_spatial_subject_read_v1 AS
SELECT
    p.subject_id,p.record_family,p.display_name,p.runtime_mode,p.visibility,
    p.publication_reference,p.geometry_id,p.geometry_version,p.read_model_version,
    g.geometry_role_code,g.crs_code,g.geometry_type_code,g.geometry,
    g.valid_from AS geometry_valid_from,g.valid_to AS geometry_valid_to
FROM geography.nngla_spatial_read_projection_v1 p
LEFT JOIN geography.nngla_geometry_version g
  ON g.geometry_id=p.geometry_id
 AND g.runtime_mode=p.runtime_mode
WHERE p.visibility='PUBLIC'
  AND (p.geometry_id IS NULL OR g.geometry_id IS NOT NULL);

CREATE OR REPLACE FUNCTION geography.nngla_current_geometry(p_subject_id text,p_runtime_mode text)
RETURNS geometry
LANGUAGE sql STABLE AS $$
    SELECT geometry
    FROM geography.nngla_spatial_subject_read_v1
    WHERE subject_id=p_subject_id AND runtime_mode=p_runtime_mode
    ORDER BY read_model_version DESC
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_contains(a text,b text,rt text,p_include_boundary boolean DEFAULT true)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT CASE WHEN p_include_boundary
   THEN ST_Covers(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
   ELSE ST_Contains(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
 END
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_within(a text,b text,rt text,p_include_boundary boolean DEFAULT true)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT CASE WHEN p_include_boundary
   THEN ST_CoveredBy(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
   ELSE ST_Within(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
 END
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_intersects(a text,b text,rt text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT ST_Intersects(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_crosses(a text,b text,rt text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT ST_Crosses(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_touches(a text,b text,rt text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT ST_Touches(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_adjacent(a text,b text,rt text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT ST_Touches(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_connected_to(a text,b text,rt text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT ST_Intersects(geography.nngla_current_geometry(a,rt),geography.nngla_current_geometry(b,rt))
$$;

CREATE OR REPLACE FUNCTION geography.nngla_query_distance(a text,b text,rt text)
RETURNS double precision LANGUAGE sql STABLE AS $$
 SELECT ST_Distance(
   geography.nngla_current_geometry(a,rt)::geography,
   geography.nngla_current_geometry(b,rt)::geography
 )
$$;

-- KNN is used only to shortlist public projected candidates. Exact metric result is geography distance.
CREATE OR REPLACE FUNCTION geography.nngla_query_nearest(p_subject_id text,p_family text,p_runtime_mode text,p_limit integer DEFAULT 1)
RETURNS TABLE(subject_id text,distance_m double precision)
LANGUAGE sql STABLE AS $$
 WITH origin AS (
   SELECT geography.nngla_current_geometry(p_subject_id,p_runtime_mode) AS g
 )
 SELECT r.subject_id,
        ST_Distance(r.geometry::geography,origin.g::geography) AS distance_m
 FROM geography.nngla_spatial_subject_read_v1 r, origin
 WHERE r.runtime_mode=p_runtime_mode
   AND r.record_family=p_family
   AND r.geometry IS NOT NULL
   AND r.subject_id<>p_subject_id
 ORDER BY r.geometry <-> origin.g
 LIMIT LEAST(GREATEST(p_limit,1),1000)
$$;

-- FRONTS comes from governed frontage evidence, never nearest-road inference.
CREATE OR REPLACE VIEW geography.nngla_road_frontage_read_v1 AS
SELECT f.frontage_id,f.site_id,f.road_id,f.road_segment_id,f.frontage_role,
       f.access_status,f.qualification_status,f.effective_from,f.effective_to
FROM geography.nngla_road_frontage f
JOIN geography.nngla_spatial_read_projection_v1 road
  ON road.subject_id=f.road_id
 AND road.visibility='PUBLIC'
WHERE f.qualification_status='PASS' AND f.effective_to IS NULL;

CREATE OR REPLACE FUNCTION geography.nngla_query_fronts(p_site_id text,p_road_id text DEFAULT NULL)
RETURNS TABLE(frontage_id text,site_id text,road_id text,road_segment_id text)
LANGUAGE sql STABLE AS $$
 SELECT f.frontage_id,f.site_id,f.road_id,f.road_segment_id
 FROM geography.nngla_road_frontage_read_v1 f
 WHERE f.site_id=p_site_id AND (p_road_id IS NULL OR f.road_id=p_road_id)
 ORDER BY f.road_id,f.frontage_id
$$;

-- Geocoding may return multiple subjects for one visible name. It is bounded by
-- the explicit public read projection rather than raw canonical name existence.
CREATE OR REPLACE VIEW geography.nngla_geocode_name_read_v1 AS
SELECT n.name_id,n.canonical_name,n.ascii_name,n.name_family,n.naming_status_code,
       a.subject_id,a.feature_type_code,a.assignment_role,a.assignment_status,
       a.effective_from,a.effective_to,p.geometry_id,p.geometry_version,p.read_model_version
FROM geography.nngla_geographic_name n
JOIN geography.nngla_name_assignment a ON a.name_id=n.name_id
JOIN geography.nngla_spatial_read_projection_v1 p
  ON p.subject_id=a.subject_id AND p.visibility='PUBLIC'
WHERE a.effective_to IS NULL;

CREATE OR REPLACE FUNCTION geography.nngla_reverse_geocode(p_longitude double precision,p_latitude double precision,p_runtime_mode text)
RETURNS TABLE(subject_id text,record_family text,geometry_id text,geometry_version integer)
LANGUAGE sql STABLE AS $$
 SELECT r.subject_id,r.record_family,r.geometry_id,r.geometry_version
 FROM geography.nngla_spatial_subject_read_v1 r
 WHERE r.runtime_mode=p_runtime_mode
   AND r.geometry IS NOT NULL
   AND ST_Intersects(r.geometry,ST_SetSRID(ST_Point(p_longitude,p_latitude),4326))
 ORDER BY r.record_family,r.subject_id
$$;
