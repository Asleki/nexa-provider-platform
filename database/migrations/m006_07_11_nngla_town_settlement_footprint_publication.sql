BEGIN;

-- P006.7.11.15.9.3 - TOWN Settlement-Footprint Truth & Publication
-- Bundle19A settlement footprints are evidence only. The database is runtime authority.
-- Source-contract fields are persisted for audit; publication is fail-closed.

CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_town_settlement_footprint_record (
    town_footprint_id text PRIMARY KEY CHECK (town_footprint_id LIKE 'town-footprint:nngla:%'),
    place_id text NOT NULL REFERENCES geography.nngla_place_reference(place_id) ON DELETE RESTRICT,
    parent_place_id text REFERENCES geography.nngla_place_reference(place_id) ON DELETE RESTRICT,
    canonical_name text NOT NULL CHECK (btrim(canonical_name) <> ''),
    source_place_code text NOT NULL CHECK (btrim(source_place_code) <> ''),
    parent_source_place_code text NOT NULL CHECK (btrim(parent_source_place_code) <> ''),
    geometry_role_code text NOT NULL CHECK (geometry_role_code='SETTLEMENT_FOOTPRINT'),
    legal_boundary_status text NOT NULL CHECK (btrim(legal_boundary_status) <> ''),
    source_qualification_status text NOT NULL CHECK (btrim(source_qualification_status) <> ''),
    source_dataset_id text NOT NULL CHECK (btrim(source_dataset_id) <> ''),
    source_dataset_version text NOT NULL CHECK (btrim(source_dataset_version) <> ''),
    source_generation_method text NOT NULL CHECK (btrim(source_generation_method) <> ''),
    source_runtime_effect_scope text NOT NULL CHECK (btrim(source_runtime_effect_scope) <> ''),
    source_path_reference text NOT NULL CHECK (btrim(source_path_reference) <> ''),
    source_dataset_sha256 text NOT NULL CHECK (source_dataset_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
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
    UNIQUE (town_footprint_id,place_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (NOT ST_IsEmpty(geometry) AND ST_IsValid(geometry) AND ST_SRID(geometry)=4326),
    CHECK (ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')),
    CHECK (NOT ST_IsEmpty(label_point) AND ST_IsValid(label_point) AND ST_SRID(label_point)=4326 AND ST_CoveredBy(label_point,geometry))
);
CREATE UNIQUE INDEX ux_nngla_town_footprint_current ON geography.nngla_town_settlement_footprint_record(place_id) WHERE effective_to IS NULL AND qualification_status='QUALIFIED';
CREATE UNIQUE INDEX ux_nngla_town_footprint_geometry_sha256 ON geography.nngla_town_settlement_footprint_record(geometry_sha256);
CREATE INDEX ix_nngla_town_footprint_parent ON geography.nngla_town_settlement_footprint_record(parent_place_id);
CREATE INDEX ix_nngla_town_footprint_source ON geography.nngla_town_settlement_footprint_record(source_dataset_id,source_place_code);
CREATE INDEX ix_nngla_town_footprint_geometry_gist ON geography.nngla_town_settlement_footprint_record USING gist(geometry);
CREATE INDEX ix_nngla_town_footprint_label_gist ON geography.nngla_town_settlement_footprint_record USING gist(label_point);

CREATE TABLE geography.nngla_town_footprint_qualification (
    qualification_id text PRIMARY KEY CHECK (qualification_id LIKE 'town-footprint-qualification:nngla:%'),
    place_id text NOT NULL REFERENCES geography.nngla_place_reference(place_id) ON DELETE RESTRICT,
    town_footprint_id text NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    is_valid boolean NOT NULL,
    is_non_empty boolean NOT NULL,
    is_polygonal boolean NOT NULL,
    identity_parentage_match boolean NOT NULL,
    source_contract_match boolean NOT NULL,
    qualification_status text NOT NULL CHECK (qualification_status IN ('QUALIFIED','REJECTED')),
    policy_version integer NOT NULL DEFAULT 1 CHECK (policy_version=1),
    qualified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (place_id,town_footprint_id),
    FOREIGN KEY (town_footprint_id,place_id) REFERENCES geography.nngla_town_settlement_footprint_record(town_footprint_id,place_id) ON DELETE RESTRICT,
    CHECK (qualification_status <> 'QUALIFIED' OR (is_valid AND is_non_empty AND is_polygonal AND identity_parentage_match AND source_contract_match AND qualified_at IS NOT NULL))
);
CREATE INDEX ix_nngla_town_footprint_qualification_place ON geography.nngla_town_footprint_qualification(place_id,qualification_status);

CREATE TABLE geography.nngla_town_publication (
    publication_id text PRIMARY KEY CHECK (publication_id LIKE 'town-publication:nngla:%'),
    place_id text NOT NULL REFERENCES geography.nngla_place_reference(place_id) ON DELETE RESTRICT,
    town_footprint_id text NOT NULL,
    qualification_id text NOT NULL REFERENCES geography.nngla_town_footprint_qualification(qualification_id) ON DELETE RESTRICT,
    publication_status text NOT NULL CHECK (publication_status IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publication_status <> 'PUBLISHED' OR published_at IS NOT NULL),
    FOREIGN KEY (town_footprint_id,place_id) REFERENCES geography.nngla_town_settlement_footprint_record(town_footprint_id,place_id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX ux_nngla_town_publication_current ON geography.nngla_town_publication(place_id) WHERE publication_status='PUBLISHED';
CREATE INDEX ix_nngla_town_publication_footprint ON geography.nngla_town_publication(town_footprint_id,publication_status);

CREATE VIEW geography.nngla_town_public_read_v1 AS
SELECT p.place_id,parent_place.place_id AS parent_place_id,n.canonical_name,p.place_type_code,
       f.town_footprint_id,f.source_place_code,f.parent_source_place_code,f.geometry_role_code,f.legal_boundary_status,
       f.source_qualification_status,f.source_dataset_id,f.source_dataset_version,f.source_generation_method,f.source_runtime_effect_scope,
       f.source_path_reference,f.source_dataset_sha256,f.source_geometry_sha256,f.realization_version,f.geometry_type_code,f.crs_code,
       f.area_m2,f.area_km2,f.perimeter_m,f.perimeter_km,ST_Y(f.label_point) AS label_latitude,ST_X(f.label_point) AS label_longitude,
       f.geometry,f.geometry_sha256,q.qualification_id,q.qualification_status,pub.publication_id,pub.publication_status,pub.published_at
FROM geography.nngla_place_reference p
JOIN geography.nngla_geographic_name n ON n.name_id=p.settlement_name_record_id
LEFT JOIN geography.nngla_place_reference parent_place ON parent_place.source_place_code=p.parent_source_place_code
JOIN geography.nngla_town_settlement_footprint_record f ON f.place_id=p.place_id AND f.effective_to IS NULL AND f.qualification_status='QUALIFIED'
JOIN geography.nngla_town_footprint_qualification q ON q.place_id=p.place_id AND q.town_footprint_id=f.town_footprint_id AND q.geometry_sha256=f.geometry_sha256 AND q.qualification_status='QUALIFIED'
JOIN geography.nngla_town_publication pub ON pub.place_id=p.place_id AND pub.town_footprint_id=f.town_footprint_id AND pub.qualification_id=q.qualification_id AND pub.publication_status='PUBLISHED'
WHERE upper(p.place_type_code)='TOWN'
  AND f.canonical_name=n.canonical_name
  AND f.source_place_code=p.source_place_code
  AND f.parent_source_place_code=COALESCE(p.parent_source_place_code,'')
  AND f.geometry_role_code='SETTLEMENT_FOOTPRINT'
  AND f.source_qualification_status='QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY'
  AND q.is_valid AND q.is_non_empty AND q.is_polygonal AND q.identity_parentage_match AND q.source_contract_match
  AND ST_CoveredBy(f.label_point,f.geometry);

COMMIT;
