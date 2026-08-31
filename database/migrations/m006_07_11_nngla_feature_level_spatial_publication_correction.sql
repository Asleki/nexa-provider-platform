BEGIN;

-- P006.7.11.15.9 corrective migration, sequence 29.
--
-- Migrations 26-28 are already applied and checksummed and MUST NOT be edited.
-- This successor restores the intended separation:
--
-- FEATURE_QUALIFIED  = the individual feature is valid, provenance-bound,
--                      exactly contained by its authoritative parent, and has
--                      no positive-area conflict affecting that feature.
-- FABRIC_COMPLETE    = all siblings collectively exhaust their parent exactly.
-- PUBLICATION        = governed feature qualification + publication approval.
--
-- Fabric completeness remains auditable and fail-closed, but it no longer
-- gates independent publication of a qualified feature.

CREATE SCHEMA IF NOT EXISTS geography;

-- ---------------------------------------------------------------------------
-- MUNICIPALITY feature qualification/publication successor contract
-- ---------------------------------------------------------------------------

CREATE TABLE geography.nngla_municipality_feature_qualification (
    feature_qualification_id text PRIMARY KEY
        CHECK (feature_qualification_id LIKE 'municipality-feature-qualification:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    municipality_geometry_id text NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
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
    identity_parentage_match boolean NOT NULL,
    source_contract_match boolean NOT NULL,
    is_valid boolean NOT NULL,
    is_non_empty boolean NOT NULL,
    is_polygonal boolean NOT NULL,
    covered_by_parent_region boolean NOT NULL,
    city_positive_overlap_m2 double precision NOT NULL
        CHECK (city_positive_overlap_m2 >= 0),
    municipality_sibling_positive_overlap_m2 double precision NOT NULL
        CHECK (municipality_sibling_positive_overlap_m2 >= 0),
    feature_fingerprint_sha256 text NOT NULL
        CHECK (feature_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
    qualification_status text NOT NULL
        CHECK (qualification_status IN ('QUALIFIED','REJECTED')),
    rejection_code text,
    policy_version integer NOT NULL DEFAULT 2 CHECK (policy_version=2),
    qualified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (administrative_area_id, municipality_geometry_id),
    FOREIGN KEY (municipality_geometry_id, administrative_area_id)
        REFERENCES geography.nngla_municipality_geometry_record(
            municipality_geometry_id, administrative_area_id
        ) ON DELETE RESTRICT,
    CHECK (
        qualification_status <> 'QUALIFIED'
        OR (
            identity_parentage_match
            AND source_contract_match
            AND is_valid
            AND is_non_empty
            AND is_polygonal
            AND covered_by_parent_region
            AND city_positive_overlap_m2=0
            AND municipality_sibling_positive_overlap_m2=0
            AND rejection_code IS NULL
            AND qualified_at IS NOT NULL
        )
    ),
    CHECK (
        qualification_status <> 'REJECTED'
        OR rejection_code IS NOT NULL
    )
);

CREATE UNIQUE INDEX ux_nngla_municipality_feature_qualification_fingerprint
ON geography.nngla_municipality_feature_qualification(feature_fingerprint_sha256);

CREATE INDEX ix_nngla_municipality_feature_qualification_parent
ON geography.nngla_municipality_feature_qualification(
    parent_region_id, parent_region_geometry_id, qualification_status
);

CREATE TABLE geography.nngla_municipality_feature_publication (
    publication_id text PRIMARY KEY
        CHECK (publication_id LIKE 'municipality-feature-publication:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    municipality_geometry_id text NOT NULL,
    feature_qualification_id text NOT NULL
        REFERENCES geography.nngla_municipality_feature_qualification(
            feature_qualification_id
        ) ON DELETE RESTRICT,
    publication_status text NOT NULL
        CHECK (publication_status IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publication_status <> 'PUBLISHED' OR published_at IS NOT NULL),
    FOREIGN KEY (municipality_geometry_id, administrative_area_id)
        REFERENCES geography.nngla_municipality_geometry_record(
            municipality_geometry_id, administrative_area_id
        ) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX ux_nngla_municipality_feature_publication_current
ON geography.nngla_municipality_feature_publication(administrative_area_id)
WHERE publication_status='PUBLISHED';

CREATE INDEX ix_nngla_municipality_feature_publication_geometry
ON geography.nngla_municipality_feature_publication(
    municipality_geometry_id, publication_status
);

-- ---------------------------------------------------------------------------
-- CITY_DISTRICT feature qualification/publication successor contract
-- ---------------------------------------------------------------------------

CREATE TABLE geography.nngla_city_district_feature_qualification (
    feature_qualification_id text PRIMARY KEY
        CHECK (feature_qualification_id LIKE 'city-district-feature-qualification:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    district_geometry_id text NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    parent_city_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    parent_city_geometry_id text NOT NULL
        REFERENCES geography.nngla_city_geometry_record(city_geometry_id)
        ON DELETE RESTRICT,
    parent_city_geometry_sha256 text NOT NULL
        CHECK (parent_city_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    identity_parentage_match boolean NOT NULL,
    source_contract_match boolean NOT NULL,
    is_valid boolean NOT NULL,
    is_non_empty boolean NOT NULL,
    is_polygonal boolean NOT NULL,
    covered_by_parent_city boolean NOT NULL,
    sibling_positive_overlap_m2 double precision NOT NULL
        CHECK (sibling_positive_overlap_m2 >= 0),
    feature_fingerprint_sha256 text NOT NULL
        CHECK (feature_fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
    qualification_status text NOT NULL
        CHECK (qualification_status IN ('QUALIFIED','REJECTED')),
    rejection_code text,
    policy_version integer NOT NULL DEFAULT 2 CHECK (policy_version=2),
    qualified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (administrative_area_id, district_geometry_id),
    FOREIGN KEY (district_geometry_id, administrative_area_id)
        REFERENCES geography.nngla_city_district_geometry_record(
            district_geometry_id, administrative_area_id
        ) ON DELETE RESTRICT,
    CHECK (
        qualification_status <> 'QUALIFIED'
        OR (
            identity_parentage_match
            AND source_contract_match
            AND is_valid
            AND is_non_empty
            AND is_polygonal
            AND covered_by_parent_city
            AND sibling_positive_overlap_m2=0
            AND rejection_code IS NULL
            AND qualified_at IS NOT NULL
        )
    ),
    CHECK (
        qualification_status <> 'REJECTED'
        OR rejection_code IS NOT NULL
    )
);

CREATE UNIQUE INDEX ux_nngla_city_district_feature_qualification_fingerprint
ON geography.nngla_city_district_feature_qualification(feature_fingerprint_sha256);

CREATE INDEX ix_nngla_city_district_feature_qualification_parent
ON geography.nngla_city_district_feature_qualification(
    parent_city_id, parent_city_geometry_id, qualification_status
);

CREATE TABLE geography.nngla_city_district_feature_publication (
    publication_id text PRIMARY KEY
        CHECK (publication_id LIKE 'city-district-feature-publication:nngla:%'),
    administrative_area_id text NOT NULL
        REFERENCES geography.nngla_administrative_area(administrative_area_id)
        ON DELETE RESTRICT,
    district_geometry_id text NOT NULL,
    feature_qualification_id text NOT NULL
        REFERENCES geography.nngla_city_district_feature_qualification(
            feature_qualification_id
        ) ON DELETE RESTRICT,
    publication_status text NOT NULL
        CHECK (publication_status IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publication_status <> 'PUBLISHED' OR published_at IS NOT NULL),
    FOREIGN KEY (district_geometry_id, administrative_area_id)
        REFERENCES geography.nngla_city_district_geometry_record(
            district_geometry_id, administrative_area_id
        ) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX ux_nngla_city_district_feature_publication_current
ON geography.nngla_city_district_feature_publication(administrative_area_id)
WHERE publication_status='PUBLISHED';

CREATE INDEX ix_nngla_city_district_feature_publication_geometry
ON geography.nngla_city_district_feature_publication(
    district_geometry_id, publication_status
);

-- ---------------------------------------------------------------------------
-- Live fabric completeness views. These remain separate from publication.
-- Existing sequence-26/27 partition tables remain intact for persisted evidence.
-- ---------------------------------------------------------------------------

CREATE VIEW geography.nngla_city_district_fabric_status_read_v2 AS
WITH current_feature AS (
    SELECT
        g.administrative_area_id,
        g.parent_city_id,
        g.parent_city_geometry_id,
        g.parent_city_geometry_sha256,
        g.geometry
    FROM geography.nngla_city_district_geometry_record AS g
    JOIN geography.nngla_city_district_feature_qualification AS q
      ON q.administrative_area_id=g.administrative_area_id
     AND q.district_geometry_id=g.district_geometry_id
     AND q.geometry_sha256=g.geometry_sha256
     AND q.parent_city_id=g.parent_city_id
     AND q.parent_city_geometry_id=g.parent_city_geometry_id
     AND q.parent_city_geometry_sha256=g.parent_city_geometry_sha256
     AND q.qualification_status='QUALIFIED'
    WHERE g.effective_to IS NULL
      AND g.qualification_status='QUALIFIED'
), grouped AS (
    SELECT
        parent_city_id,
        parent_city_geometry_id,
        parent_city_geometry_sha256,
        count(*)::integer AS observed_district_count,
        ST_UnaryUnion(ST_Collect(geometry)) AS district_union,
        bool_and(ST_IsValid(geometry)) AS all_valid,
        bool_and(NOT ST_IsEmpty(geometry)) AS all_non_empty,
        bool_and(ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')) AS all_polygonal
    FROM current_feature
    GROUP BY parent_city_id,parent_city_geometry_id,parent_city_geometry_sha256
), overlap AS (
    SELECT
        a.parent_city_id,
        COALESCE(sum(
            ST_Area(
                ST_CollectionExtract(
                    ST_Intersection(a.geometry,b.geometry),3
                )::geography
            )
        ),0.0) AS sibling_positive_overlap_m2
    FROM current_feature AS a
    JOIN current_feature AS b
      ON b.parent_city_id=a.parent_city_id
     AND a.administrative_area_id < b.administrative_area_id
    GROUP BY a.parent_city_id
)
SELECT
    c.city_id AS parent_city_id,
    c.city_geometry_id AS parent_city_geometry_id,
    c.geometry_sha256 AS parent_city_geometry_sha256,
    8::integer AS expected_district_count,
    COALESCE(g.observed_district_count,0)::integer AS observed_district_count,
    COALESCE(g.all_valid,true) AS all_valid,
    COALESCE(g.all_non_empty,true) AS all_non_empty,
    COALESCE(g.all_polygonal,true) AS all_polygonal,
    COALESCE(o.sibling_positive_overlap_m2,0.0) AS sibling_positive_overlap_m2,
    CASE
      WHEN g.district_union IS NULL THEN false
      ELSE ST_Equals(g.district_union,c.geometry)
    END AS union_equals_city,
    COALESCE(ST_Area(g.district_union::geography),0.0) AS union_area_m2,
    ST_Area(c.geometry::geography) AS city_area_m2,
    CASE
      WHEN g.district_union IS NULL THEN ST_Area(c.geometry::geography)
      ELSE ST_Area(
        ST_CollectionExtract(
          ST_SymDifference(g.district_union,c.geometry),3
        )::geography
      )
    END AS symmetric_difference_m2,
    CASE
      WHEN COALESCE(g.observed_district_count,0)=8
       AND COALESCE(g.all_valid,true)
       AND COALESCE(g.all_non_empty,true)
       AND COALESCE(g.all_polygonal,true)
       AND COALESCE(o.sibling_positive_overlap_m2,0.0)=0
       AND g.district_union IS NOT NULL
       AND ST_Equals(g.district_union,c.geometry)
      THEN 'COMPLETE'
      ELSE 'PARTIAL'
    END AS fabric_status
FROM geography.nngla_city_public_read_v1 AS c
LEFT JOIN grouped AS g
  ON g.parent_city_id=c.city_id
 AND g.parent_city_geometry_id=c.city_geometry_id
 AND g.parent_city_geometry_sha256=c.geometry_sha256
LEFT JOIN overlap AS o
  ON o.parent_city_id=c.city_id
WHERE c.administrative_type_code='CITY'
  AND c.qualification_status='QUALIFIED'
  AND c.publication_status='PUBLISHED';

CREATE VIEW geography.nngla_municipality_fabric_status_read_v2 AS
WITH current_feature AS (
    SELECT
        g.administrative_area_id,
        g.parent_region_id,
        g.parent_region_geometry_id,
        g.parent_region_geometry_sha256,
        q.city_id,
        q.city_geometry_id,
        q.city_geometry_sha256,
        g.geometry
    FROM geography.nngla_municipality_geometry_record AS g
    JOIN geography.nngla_municipality_feature_qualification AS q
      ON q.administrative_area_id=g.administrative_area_id
     AND q.municipality_geometry_id=g.municipality_geometry_id
     AND q.geometry_sha256=g.geometry_sha256
     AND q.parent_region_id=g.parent_region_id
     AND q.parent_region_geometry_id=g.parent_region_geometry_id
     AND q.parent_region_geometry_sha256=g.parent_region_geometry_sha256
     AND q.qualification_status='QUALIFIED'
    WHERE g.effective_to IS NULL
      AND g.qualification_status='QUALIFIED'
), grouped AS (
    SELECT
        parent_region_id,
        parent_region_geometry_id,
        parent_region_geometry_sha256,
        city_id,
        city_geometry_id,
        city_geometry_sha256,
        count(*)::integer AS observed_municipality_count,
        ST_UnaryUnion(ST_Collect(geometry)) AS municipality_union,
        bool_and(ST_IsValid(geometry)) AS all_valid,
        bool_and(NOT ST_IsEmpty(geometry)) AS all_non_empty,
        bool_and(ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')) AS all_polygonal
    FROM current_feature
    GROUP BY
        parent_region_id,parent_region_geometry_id,parent_region_geometry_sha256,
        city_id,city_geometry_id,city_geometry_sha256
), sibling_overlap AS (
    SELECT
        a.parent_region_id,
        COALESCE(sum(
            ST_Area(
                ST_CollectionExtract(
                    ST_Intersection(a.geometry,b.geometry),3
                )::geography
            )
        ),0.0) AS municipality_sibling_positive_overlap_m2
    FROM current_feature AS a
    JOIN current_feature AS b
      ON b.parent_region_id=a.parent_region_id
     AND a.administrative_area_id < b.administrative_area_id
    GROUP BY a.parent_region_id
), city_overlap AS (
    SELECT
        m.parent_region_id,
        COALESCE(sum(
            ST_Area(
                ST_CollectionExtract(
                    ST_Intersection(m.geometry,c.geometry),3
                )::geography
            )
        ),0.0) AS city_municipality_positive_overlap_m2
    FROM current_feature AS m
    JOIN geography.nngla_city_public_read_v1 AS c
      ON c.city_id=m.city_id
     AND c.city_geometry_id=m.city_geometry_id
     AND c.geometry_sha256=m.city_geometry_sha256
    GROUP BY m.parent_region_id
)
SELECT
    r.region_id AS parent_region_id,
    r.region_geometry_id AS parent_region_geometry_id,
    r.geometry_sha256 AS parent_region_geometry_sha256,
    c.city_id,
    c.city_geometry_id,
    c.geometry_sha256 AS city_geometry_sha256,
    3::integer AS expected_municipality_count,
    COALESCE(g.observed_municipality_count,0)::integer AS observed_municipality_count,
    COALESCE(g.all_valid,true) AS all_valid,
    COALESCE(g.all_non_empty,true) AS all_non_empty,
    COALESCE(g.all_polygonal,true) AS all_polygonal,
    COALESCE(s.municipality_sibling_positive_overlap_m2,0.0)
      AS municipality_sibling_positive_overlap_m2,
    COALESCE(co.city_municipality_positive_overlap_m2,0.0)
      AS city_municipality_positive_overlap_m2,
    CASE
      WHEN g.municipality_union IS NULL THEN false
      ELSE ST_Equals(
        ST_UnaryUnion(ST_Collect(c.geometry,g.municipality_union)),
        r.geometry
      )
    END AS union_equals_region,
    CASE
      WHEN g.municipality_union IS NULL THEN ST_Area(c.geometry::geography)
      ELSE ST_Area(
        ST_UnaryUnion(ST_Collect(c.geometry,g.municipality_union))::geography
      )
    END AS union_area_m2,
    ST_Area(r.geometry::geography) AS region_area_m2,
    CASE
      WHEN g.municipality_union IS NULL THEN ST_Area(
        ST_CollectionExtract(ST_SymDifference(c.geometry,r.geometry),3)::geography
      )
      ELSE ST_Area(
        ST_CollectionExtract(
          ST_SymDifference(
            ST_UnaryUnion(ST_Collect(c.geometry,g.municipality_union)),
            r.geometry
          ),3
        )::geography
      )
    END AS symmetric_difference_m2,
    CASE
      WHEN COALESCE(g.observed_municipality_count,0)=3
       AND COALESCE(g.all_valid,true)
       AND COALESCE(g.all_non_empty,true)
       AND COALESCE(g.all_polygonal,true)
       AND COALESCE(s.municipality_sibling_positive_overlap_m2,0.0)=0
       AND COALESCE(co.city_municipality_positive_overlap_m2,0.0)=0
       AND g.municipality_union IS NOT NULL
       AND ST_Equals(
         ST_UnaryUnion(ST_Collect(c.geometry,g.municipality_union)),
         r.geometry
       )
      THEN 'COMPLETE'
      ELSE 'PARTIAL'
    END AS fabric_status
FROM geography.nngla_region_public_read_v1 AS r
JOIN geography.nngla_city_public_read_v1 AS c
  ON c.parent_region_id=r.region_id
 AND c.administrative_type_code='CITY'
 AND c.qualification_status='QUALIFIED'
 AND c.publication_status='PUBLISHED'
LEFT JOIN grouped AS g
  ON g.parent_region_id=r.region_id
 AND g.parent_region_geometry_id=r.region_geometry_id
 AND g.parent_region_geometry_sha256=r.geometry_sha256
 AND g.city_id=c.city_id
 AND g.city_geometry_id=c.city_geometry_id
 AND g.city_geometry_sha256=c.geometry_sha256
LEFT JOIN sibling_overlap AS s
  ON s.parent_region_id=r.region_id
LEFT JOIN city_overlap AS co
  ON co.parent_region_id=r.region_id
WHERE r.administrative_type_code='REGION'
  AND r.qualification_status='QUALIFIED'
  AND r.publication_status='PUBLISHED';

-- ---------------------------------------------------------------------------
-- Versioned public views. Feature qualification/publication gates visibility;
-- PARTIAL fabric status remains visible as metadata and never hides a child.
-- ---------------------------------------------------------------------------

CREATE VIEW geography.nngla_city_district_public_read_v2 AS
SELECT
    a.administrative_area_id AS district_id,
    g.parent_city_id,
    a.region_code,
    a.canonical_name,
    a.administrative_type_code,
    g.district_geometry_id,
    g.parent_city_geometry_id,
    g.parent_city_geometry_sha256,
    g.source_record_id,
    g.parent_source_record_id,
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
    fp.publication_id,
    fp.publication_status,
    fp.published_at
FROM geography.nngla_administrative_area AS a
JOIN geography.nngla_city_district_geometry_record AS g
  ON g.administrative_area_id=a.administrative_area_id
 AND g.effective_to IS NULL
 AND g.qualification_status='QUALIFIED'
JOIN geography.nngla_city_public_read_v1 AS c
  ON c.city_id=g.parent_city_id
 AND c.city_geometry_id=g.parent_city_geometry_id
 AND c.geometry_sha256=g.parent_city_geometry_sha256
 AND c.administrative_type_code='CITY'
 AND c.qualification_status='QUALIFIED'
 AND c.publication_status='PUBLISHED'
JOIN geography.nngla_city_district_feature_qualification AS fq
  ON fq.administrative_area_id=a.administrative_area_id
 AND fq.district_geometry_id=g.district_geometry_id
 AND fq.geometry_sha256=g.geometry_sha256
 AND fq.source_geometry_sha256=g.source_geometry_sha256
 AND fq.parent_city_id=g.parent_city_id
 AND fq.parent_city_geometry_id=g.parent_city_geometry_id
 AND fq.parent_city_geometry_sha256=g.parent_city_geometry_sha256
 AND fq.qualification_status='QUALIFIED'
JOIN geography.nngla_city_district_feature_publication AS fp
  ON fp.administrative_area_id=a.administrative_area_id
 AND fp.district_geometry_id=g.district_geometry_id
 AND fp.feature_qualification_id=fq.feature_qualification_id
 AND fp.publication_status='PUBLISHED'
LEFT JOIN geography.nngla_city_district_fabric_status_read_v2 AS fs
  ON fs.parent_city_id=g.parent_city_id
 AND fs.parent_city_geometry_id=g.parent_city_geometry_id
 AND fs.parent_city_geometry_sha256=g.parent_city_geometry_sha256
LEFT JOIN geography.nngla_city_district_partition_qualification AS pq
  ON pq.parent_city_id=g.parent_city_id
 AND pq.parent_city_geometry_id=g.parent_city_geometry_id
 AND pq.parent_city_geometry_sha256=g.parent_city_geometry_sha256
 AND pq.effective_to IS NULL
WHERE a.administrative_type_code IN ('DISTRICT','CITY_DISTRICT')
  AND g.canonical_name=a.canonical_name
  AND a.parent_source_record_id=c.source_record_id
  AND ST_CoveredBy(g.geometry,c.geometry)
  AND ST_CoveredBy(g.label_point,g.geometry)
  AND fq.identity_parentage_match
  AND fq.source_contract_match
  AND fq.is_valid
  AND fq.is_non_empty
  AND fq.is_polygonal
  AND fq.covered_by_parent_city
  AND fq.sibling_positive_overlap_m2=0
  AND EXISTS (
      SELECT 1
      FROM geography.nngla_execution_receipt AS er
      JOIN geography.nngla_execution_item AS ei
        ON ei.execution_id=er.execution_id
      WHERE er.plan_id='p006.7.11.15.9-seq29-city-district-feature-publication'
        AND er.plan_version=1
        AND er.runtime_mode='production'
        AND er.status IN ('APPLIED','REUSED')
        AND ei.canonical_id=a.administrative_area_id
        AND ei.publication_ready
        AND ei.detail->>'district_geometry_id'=g.district_geometry_id
        AND ei.detail->>'feature_qualification_id'=fq.feature_qualification_id
        AND ei.detail->>'publication_id'=fp.publication_id
        AND ei.detail->>'geometry_sha256'=g.geometry_sha256
  );

CREATE VIEW geography.nngla_municipality_public_read_v2 AS
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

CREATE VIEW geography.nngla_town_public_read_v2 AS
SELECT
    p.place_id,
    parent_place.place_id AS parent_place_id,
    parent_admin.administrative_area_id AS parent_municipality_id,
    n.canonical_name,
    p.place_type_code,
    f.town_footprint_id,
    f.source_place_code,
    f.parent_source_place_code,
    f.geometry_role_code,
    f.legal_boundary_status,
    f.source_qualification_status,
    f.source_dataset_id,
    f.source_dataset_version,
    f.source_generation_method,
    f.source_runtime_effect_scope,
    f.source_path_reference,
    f.source_dataset_sha256,
    f.source_geometry_sha256,
    f.realization_version,
    f.geometry_type_code,
    f.crs_code,
    f.area_m2,
    f.area_km2,
    f.perimeter_m,
    f.perimeter_km,
    ST_Y(f.label_point) AS label_latitude,
    ST_X(f.label_point) AS label_longitude,
    f.geometry,
    f.geometry_sha256,
    q.qualification_id,
    q.qualification_status,
    pub.publication_id,
    pub.publication_status,
    pub.published_at
FROM geography.nngla_place_reference AS p
JOIN geography.nngla_geographic_name AS n
  ON n.name_id=p.settlement_name_record_id
JOIN geography.nngla_place_reference AS parent_place
  ON parent_place.source_place_code=p.parent_source_place_code
 AND upper(parent_place.place_type_code)='MUNICIPALITY'
JOIN geography.nngla_administrative_area AS parent_admin
  ON parent_admin.source_record_id=parent_place.source_place_code
 AND parent_admin.administrative_type_code='MUNICIPALITY'
JOIN geography.nngla_municipality_public_read_v2 AS parent_municipality
  ON parent_municipality.municipality_id=parent_admin.administrative_area_id
 AND parent_municipality.qualification_status='QUALIFIED'
 AND parent_municipality.publication_status='PUBLISHED'
JOIN geography.nngla_town_settlement_footprint_record AS f
  ON f.place_id=p.place_id
 AND f.effective_to IS NULL
 AND f.qualification_status='QUALIFIED'
JOIN geography.nngla_town_footprint_qualification AS q
  ON q.place_id=p.place_id
 AND q.town_footprint_id=f.town_footprint_id
 AND q.geometry_sha256=f.geometry_sha256
 AND q.qualification_status='QUALIFIED'
JOIN geography.nngla_town_publication AS pub
  ON pub.place_id=p.place_id
 AND pub.town_footprint_id=f.town_footprint_id
 AND pub.qualification_id=q.qualification_id
 AND pub.publication_status='PUBLISHED'
WHERE upper(p.place_type_code)='TOWN'
  AND f.canonical_name=n.canonical_name
  AND f.source_place_code=p.source_place_code
  AND f.parent_source_place_code=COALESCE(p.parent_source_place_code,'')
  AND f.geometry_role_code='SETTLEMENT_FOOTPRINT'
  AND f.source_qualification_status='QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY'
  AND q.is_valid
  AND q.is_non_empty
  AND q.is_polygonal
  AND q.identity_parentage_match
  AND q.source_contract_match
  AND ST_CoveredBy(f.geometry,parent_municipality.geometry)
  AND ST_CoveredBy(f.label_point,f.geometry)
  AND EXISTS (
      SELECT 1
      FROM geography.nngla_execution_receipt AS er
      JOIN geography.nngla_execution_item AS ei
        ON ei.execution_id=er.execution_id
      WHERE er.plan_id='p006.7.11.15.9-seq29-town-feature-publication'
        AND er.plan_version=1
        AND er.runtime_mode='production'
        AND er.status IN ('APPLIED','REUSED')
        AND ei.canonical_id=p.place_id
        AND ei.publication_ready
        AND ei.detail->>'town_footprint_id'=f.town_footprint_id
        AND ei.detail->>'qualification_id'=q.qualification_id
        AND ei.detail->>'publication_id'=pub.publication_id
        AND ei.detail->>'geometry_sha256'=f.geometry_sha256
  );

COMMIT;
