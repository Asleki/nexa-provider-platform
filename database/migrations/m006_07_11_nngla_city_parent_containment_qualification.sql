BEGIN;

-- P006.7.11.15.8.1 — Deterministic CITY Parent-Containment Qualification
--
-- Additive maintenance revision for the locked CITY v1 realization path.
-- The geometry algorithm remains source reuse or exactly one intersection with
-- the exact current authoritative parent REGION.  This migration persists the
-- qualification evidence and lets the existing CITY public view accept a
-- matching QUALIFIED record when strict ST_CoveredBy alone is numerically false.

CREATE TABLE geography.nngla_city_parent_containment_qualification (
    qualification_id text PRIMARY KEY
        CHECK (qualification_id LIKE 'city-containment:nngla:%'),

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

    source_record_id text NOT NULL CHECK (btrim(source_record_id) <> ''),
    source_dataset_id text NOT NULL CHECK (btrim(source_dataset_id) <> ''),
    source_dataset_version text NOT NULL CHECK (btrim(source_dataset_version) <> ''),
    source_dataset_sha256 text NOT NULL
        CHECK (source_dataset_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL
        CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),

    realization_method text NOT NULL
        CHECK (realization_method IN ('SOURCE_REUSE','PARENT_CONTAINED_NORMALIZATION')),
    realization_version integer NOT NULL CHECK (realization_version >= 1),

    city_geometry_id text NOT NULL
        CHECK (city_geometry_id LIKE 'city-geometry:nngla:%'),
    realized_geometry_sha256 text NOT NULL
        CHECK (realized_geometry_sha256 ~ '^[0-9a-f]{64}$'),

    source_valid boolean NOT NULL,
    source_non_empty boolean NOT NULL,
    source_geometry_type text NOT NULL,
    source_strict_covered boolean NOT NULL,
    source_area_m2 double precision NOT NULL CHECK (source_area_m2 >= 0),
    source_outside_parent_m2 double precision NOT NULL
        CHECK (source_outside_parent_m2 >= 0),
    source_outside_parent_ratio double precision NOT NULL
        CHECK (source_outside_parent_ratio >= 0),

    normalized_valid boolean NOT NULL,
    normalized_non_empty boolean NOT NULL,
    normalized_geometry_type text NOT NULL,
    normalized_strict_covered boolean NOT NULL,
    normalized_area_m2 double precision NOT NULL CHECK (normalized_area_m2 >= 0),
    normalized_outside_parent_m2 double precision NOT NULL
        CHECK (normalized_outside_parent_m2 >= 0),
    normalized_outside_parent_ratio double precision NOT NULL
        CHECK (normalized_outside_parent_ratio >= 0),

    area_removed_m2 double precision NOT NULL CHECK (area_removed_m2 >= 0),
    area_removed_ratio double precision NOT NULL CHECK (area_removed_ratio >= 0),
    label_point_covered boolean NOT NULL,

    qualification_basis_code text NOT NULL
        CHECK (
            qualification_basis_code IN (
                'STRICT_SOURCE_COVERED',
                'SINGLE_INTERSECTION_STRICT_COVERED',
                'SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE',
                'SINGLE_INTERSECTION_NUMERICAL_RESIDUE',
                'REJECTED_INVALID_SOURCE',
                'REJECTED_INVALID_REALIZATION',
                'REJECTED_EMPTY_REALIZATION',
                'REJECTED_NON_POLYGONAL_REALIZATION',
                'REJECTED_LABEL_POINT',
                'REJECTED_RESIDUE_EXCEEDS_POLICY'
            )
        ),
    qualification_status text NOT NULL
        CHECK (qualification_status IN ('QUALIFIED','REJECTED')),
    qualification_policy_version integer NOT NULL
        CHECK (qualification_policy_version = 1),
    absolute_residue_max_m2 double precision NOT NULL
        CHECK (absolute_residue_max_m2 = 0.001::double precision),
    ratio_residue_max double precision NOT NULL
        CHECK (ratio_residue_max = 1e-12::double precision),

    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz NOT NULL DEFAULT now(),

    CHECK (administrative_area_id <> parent_region_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (
        source_strict_covered
        OR realization_method = 'PARENT_CONTAINED_NORMALIZATION'
    ),
    CHECK (
        realization_method <> 'SOURCE_REUSE'
        OR source_strict_covered
    ),
    CHECK (
        (qualification_status = 'QUALIFIED' AND qualification_basis_code IN (
            'STRICT_SOURCE_COVERED',
            'SINGLE_INTERSECTION_STRICT_COVERED',
            'SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE',
            'SINGLE_INTERSECTION_NUMERICAL_RESIDUE'
        ))
        OR
        (qualification_status = 'REJECTED' AND qualification_basis_code IN (
            'REJECTED_INVALID_SOURCE',
            'REJECTED_INVALID_REALIZATION',
            'REJECTED_EMPTY_REALIZATION',
            'REJECTED_NON_POLYGONAL_REALIZATION',
            'REJECTED_LABEL_POINT',
            'REJECTED_RESIDUE_EXCEEDS_POLICY'
        ))
    ),
    CHECK (
        qualification_status <> 'QUALIFIED'
        OR (
            source_valid
            AND source_non_empty
            AND normalized_valid
            AND normalized_non_empty
            AND normalized_geometry_type IN ('POLYGON','MULTIPOLYGON')
            AND normalized_area_m2 > 0
            AND label_point_covered
            AND (
                normalized_strict_covered
                OR (
                    normalized_outside_parent_m2 <= absolute_residue_max_m2
                    AND normalized_outside_parent_ratio <= ratio_residue_max
                )
            )
        )
    ),
    CHECK (
        qualification_basis_code <> 'STRICT_SOURCE_COVERED'
        OR (
            source_strict_covered
            AND normalized_strict_covered
            AND realization_method = 'SOURCE_REUSE'
        )
    ),
    CHECK (
        qualification_basis_code NOT IN (
            'SINGLE_INTERSECTION_STRICT_COVERED',
            'SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE',
            'SINGLE_INTERSECTION_NUMERICAL_RESIDUE'
        )
        OR (
            NOT source_strict_covered
            AND realization_method = 'PARENT_CONTAINED_NORMALIZATION'
        )
    ),
    CHECK (
        qualification_basis_code <> 'SINGLE_INTERSECTION_STRICT_COVERED'
        OR normalized_strict_covered
    ),
    CHECK (
        qualification_basis_code <> 'SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE'
        OR (
            NOT normalized_strict_covered
            AND normalized_outside_parent_m2 = 0
            AND normalized_outside_parent_ratio = 0
        )
    ),
    CHECK (
        qualification_basis_code <> 'SINGLE_INTERSECTION_NUMERICAL_RESIDUE'
        OR (
            NOT normalized_strict_covered
            AND normalized_outside_parent_m2 > 0
            AND normalized_outside_parent_m2 <= absolute_residue_max_m2
            AND normalized_outside_parent_ratio <= ratio_residue_max
        )
    )
);

CREATE UNIQUE INDEX ux_nngla_city_parent_containment_current
ON geography.nngla_city_parent_containment_qualification(administrative_area_id)
WHERE effective_to IS NULL;

CREATE INDEX ix_nngla_city_parent_containment_parent
ON geography.nngla_city_parent_containment_qualification(
    parent_region_id,
    parent_region_geometry_id
);

CREATE INDEX ix_nngla_city_parent_containment_geometry
ON geography.nngla_city_parent_containment_qualification(
    city_geometry_id,
    realized_geometry_sha256
);

CREATE INDEX ix_nngla_city_parent_containment_source
ON geography.nngla_city_parent_containment_qualification(
    source_dataset_id,
    source_record_id
);

CREATE VIEW geography.nngla_city_parent_containment_read_v1 AS
SELECT
    q.*,
    (
        region_geometry.region_geometry_id IS NOT NULL
        AND region_geometry.geometry_sha256 = q.parent_region_geometry_sha256
        AND region_geometry.effective_to IS NULL
        AND region_geometry.qualification_status = 'QUALIFIED'
    ) AS parent_authority_current
FROM geography.nngla_city_parent_containment_qualification AS q
LEFT JOIN geography.nngla_region_geometry_record AS region_geometry
  ON region_geometry.region_geometry_id = q.parent_region_geometry_id
 AND region_geometry.administrative_area_id = q.parent_region_id;


-- Replace only the read-policy definition.  The authoritative CITY geometry and
-- publication tables from sequence 24 are unchanged.
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
    AND (
        ST_CoveredBy(g.geometry, region_geometry.geometry)
        OR EXISTS (
            SELECT 1
            FROM geography.nngla_city_parent_containment_qualification AS q
            WHERE q.administrative_area_id = city_admin.administrative_area_id
              AND q.city_geometry_id = g.city_geometry_id
              AND q.realized_geometry_sha256 = g.geometry_sha256
              AND q.parent_region_id = g.parent_region_id
              AND q.parent_region_geometry_id = g.parent_region_geometry_id
              AND q.parent_region_geometry_sha256 = g.parent_region_geometry_sha256
              AND q.realization_method = g.realization_method
              AND q.realization_version = g.realization_version
              AND q.effective_to IS NULL
              AND q.qualification_status = 'QUALIFIED'
              AND q.normalized_valid
              AND q.normalized_non_empty
              AND q.label_point_covered
              AND (
                    q.normalized_strict_covered
                    OR (
                        q.normalized_outside_parent_m2 <= q.absolute_residue_max_m2
                        AND q.normalized_outside_parent_ratio <= q.ratio_residue_max
                    )
              )
        )
    )
    AND ST_CoveredBy(g.label_point, g.geometry)
    AND g.area_m2 > 0
    AND g.perimeter_m > 0;

COMMIT;
