BEGIN;
-- P006.7.11.15.5 Delivery 3 R1 — feature-level CITY qualification,
-- governed administrative authority adoption and initial CITY publication.
-- Delivery-1/2 evidence remains immutable. Qualification commands are SELECT-only;
-- durable qualification is written only inside an explicitly approved adoption.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_city_feature_qualification (
    qualification_id text PRIMARY KEY CHECK (qualification_id LIKE 'city-qualification:nngla:%'),
    city_administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    root_place_id text NOT NULL CHECK (root_place_id ~ '^NG-PLC-[0-9]{6}$'),
    candidate_source_mode text NOT NULL CHECK (candidate_source_mode IN ('FROZEN_SOURCE_REUSE','SHARED_FACE_RECONSTRUCTION')),
    candidate_id text NOT NULL,
    raw_candidate_geometry_sha256 text NOT NULL CHECK (raw_candidate_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    evaluated_candidate_geometry_sha256 text NOT NULL CHECK (evaluated_candidate_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    source_geometry_sha256 text NOT NULL CHECK (source_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    source_dataset_id text NOT NULL,
    source_dataset_version text NOT NULL,
    source_path_reference text NOT NULL,
    fabric_run_id text,
    package_sha256 text CHECK (package_sha256 IS NULL OR package_sha256 ~ '^[0-9a-f]{64}$'),
    validation_parent_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_evidence_kind text NOT NULL,
    parent_evidence_id text NOT NULL,
    raw_parent_geometry_sha256 text NOT NULL CHECK (raw_parent_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    evaluated_parent_geometry_sha256 text NOT NULL CHECK (evaluated_parent_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    parent_qualification_reference text NOT NULL,
    parent_source_path_reference text NOT NULL,
    peer_evidence_digest text NOT NULL CHECK (peer_evidence_digest ~ '^[0-9a-f]{64}$'),
    precision_policy_id text NOT NULL,
    precision_policy_sha256 text NOT NULL CHECK (precision_policy_sha256 ~ '^[0-9a-f]{64}$'),
    precision_mode text NOT NULL CHECK (precision_mode IN ('SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP','GOVERNED_COMMON_PRECISION')),
    precision_grid_size_degrees double precision,
    precision_evidence_reference text NOT NULL,
    valid_geometry boolean NOT NULL,
    polygonal boolean NOT NULL,
    non_empty boolean NOT NULL,
    srid_correct boolean NOT NULL,
    parent_evidence_valid boolean NOT NULL,
    city_covered_by_parent boolean NOT NULL,
    raw_area_outside_parent_m2 double precision NOT NULL CHECK (raw_area_outside_parent_m2 >= 0),
    area_outside_parent_m2 double precision NOT NULL CHECK (area_outside_parent_m2 >= 0),
    raw_positive_city_peer_overlap_m2 double precision NOT NULL CHECK (raw_positive_city_peer_overlap_m2 >= 0),
    positive_city_peer_overlap_m2 double precision NOT NULL CHECK (positive_city_peer_overlap_m2 >= 0),
    raw_positive_municipality_overlap_m2 double precision NOT NULL CHECK (raw_positive_municipality_overlap_m2 >= 0),
    positive_municipality_overlap_m2 double precision NOT NULL CHECK (positive_municipality_overlap_m2 >= 0),
    reference_point_covered boolean NOT NULL,
    unresolved_city_affecting_defect_count integer NOT NULL CHECK (unresolved_city_affecting_defect_count >= 0),
    numerical_residue boolean NOT NULL,
    source_provenance_bound boolean NOT NULL,
    qualifier_actor_id text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode='production'),
    feature_qualification_status text NOT NULL CHECK (feature_qualification_status='FEATURE_QUALIFIED'),
    qualification_sha256 text NOT NULL UNIQUE CHECK (qualification_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((candidate_source_mode='SHARED_FACE_RECONSTRUCTION') = (fabric_run_id IS NOT NULL AND package_sha256 IS NOT NULL)),
    CHECK ((precision_mode='SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP' AND precision_grid_size_degrees IS NULL)
        OR (precision_mode='GOVERNED_COMMON_PRECISION' AND precision_grid_size_degrees > 0)),
    CHECK (valid_geometry AND polygonal AND non_empty AND srid_correct AND parent_evidence_valid
        AND city_covered_by_parent AND area_outside_parent_m2=0
        AND positive_city_peer_overlap_m2=0 AND reference_point_covered
        AND unresolved_city_affecting_defect_count=0 AND source_provenance_bound)
);
CREATE INDEX ix_nngla_city_feature_qualification_subject
ON geography.nngla_city_feature_qualification(city_administrative_area_id,created_at DESC);

CREATE TABLE geography.nngla_administrative_geometry_adoption_decision (
    adoption_decision_id text PRIMARY KEY CHECK (adoption_decision_id LIKE 'authority-adoption:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    qualification_id text NOT NULL REFERENCES geography.nngla_city_feature_qualification(qualification_id) ON DELETE RESTRICT,
    qualification_sha256 text NOT NULL CHECK (qualification_sha256 ~ '^[0-9a-f]{64}$'),
    candidate_source_mode text NOT NULL CHECK (candidate_source_mode IN ('FROZEN_SOURCE_REUSE','SHARED_FACE_RECONSTRUCTION')),
    candidate_id text NOT NULL,
    candidate_geometry_sha256 text NOT NULL CHECK (candidate_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    validation_parent_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_evidence_id text NOT NULL,
    parent_geometry_sha256 text NOT NULL CHECK (parent_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    parent_qualification_reference text NOT NULL,
    peer_evidence_digest text NOT NULL CHECK (peer_evidence_digest ~ '^[0-9a-f]{64}$'),
    precision_policy_id text NOT NULL,
    precision_policy_sha256 text NOT NULL CHECK (precision_policy_sha256 ~ '^[0-9a-f]{64}$'),
    effective_on date NOT NULL,
    qualifier_actor_id text NOT NULL,
    submitter_actor_id text NOT NULL,
    approver_actor_id text NOT NULL,
    decision_reference text NOT NULL,
    rationale text NOT NULL,
    decision_status text NOT NULL CHECK (decision_status IN ('APPROVED','REJECTED','SUPERSEDED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (qualifier_actor_id <> submitter_actor_id AND qualifier_actor_id <> approver_actor_id AND submitter_actor_id <> approver_actor_id)
);
CREATE INDEX ix_nngla_admin_adoption_subject
ON geography.nngla_administrative_geometry_adoption_decision(administrative_area_id,effective_on);

CREATE TABLE geography.nngla_administrative_geometry_assignment (
    assignment_id text PRIMARY KEY CHECK (assignment_id LIKE 'admin-geometry-assignment:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    geometry_id text NOT NULL REFERENCES geography.nngla_geometry_version(geometry_id) ON DELETE RESTRICT,
    candidate_id text NOT NULL,
    qualification_id text NOT NULL REFERENCES geography.nngla_city_feature_qualification(qualification_id) ON DELETE RESTRICT,
    adoption_decision_id text NOT NULL REFERENCES geography.nngla_administrative_geometry_adoption_decision(adoption_decision_id) ON DELETE RESTRICT,
    validation_parent_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    parent_evidence_id text NOT NULL,
    parent_geometry_sha256 text NOT NULL CHECK (parent_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    effective_from date NOT NULL,
    effective_to date,
    assignment_status text NOT NULL CHECK (assignment_status IN ('EFFECTIVE','SUPERSEDED','REVOKED')),
    assignment_sha256 text NOT NULL UNIQUE CHECK (assignment_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE UNIQUE INDEX ux_nngla_admin_geometry_assignment_current
ON geography.nngla_administrative_geometry_assignment(administrative_area_id)
WHERE effective_to IS NULL AND assignment_status='EFFECTIVE';
CREATE INDEX ix_nngla_admin_geometry_assignment_geometry
ON geography.nngla_administrative_geometry_assignment(geometry_id,assignment_status);

CREATE TABLE geography.nngla_administrative_legalization_decision (
    legalization_id text PRIMARY KEY CHECK (legalization_id LIKE 'admin-legalization:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    geometry_id text NOT NULL REFERENCES geography.nngla_geometry_version(geometry_id) ON DELETE RESTRICT,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    candidate_id text NOT NULL,
    qualification_id text NOT NULL REFERENCES geography.nngla_city_feature_qualification(qualification_id) ON DELETE RESTRICT,
    assignment_id text NOT NULL REFERENCES geography.nngla_administrative_geometry_assignment(assignment_id) ON DELETE RESTRICT,
    effective_on date NOT NULL,
    submitter_actor_id text NOT NULL,
    approver_actor_id text NOT NULL,
    decision_reference text NOT NULL,
    decision_status text NOT NULL CHECK (decision_status IN ('LEGALIZED','REJECTED','SUPERSEDED')),
    decision_sha256 text NOT NULL UNIQUE CHECK (decision_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (submitter_actor_id <> approver_actor_id)
);

CREATE TABLE geography.nngla_city_authority_receipt (
    receipt_id text PRIMARY KEY CHECK (receipt_id LIKE 'city-authority-receipt:nngla:%'),
    administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    geometry_id text NOT NULL REFERENCES geography.nngla_geometry_version(geometry_id) ON DELETE RESTRICT,
    qualification_id text NOT NULL REFERENCES geography.nngla_city_feature_qualification(qualification_id) ON DELETE RESTRICT,
    adoption_decision_id text NOT NULL REFERENCES geography.nngla_administrative_geometry_adoption_decision(adoption_decision_id) ON DELETE RESTRICT,
    assignment_id text NOT NULL REFERENCES geography.nngla_administrative_geometry_assignment(assignment_id) ON DELETE RESTRICT,
    legalization_id text NOT NULL REFERENCES geography.nngla_administrative_legalization_decision(legalization_id) ON DELETE RESTRICT,
    transaction_sha256 text NOT NULL UNIQUE CHECK (transaction_sha256 ~ '^[0-9a-f]{64}$'),
    runtime_mode text NOT NULL CHECK (runtime_mode='production'),
    status text NOT NULL CHECK (status IN ('APPLIED','REUSED')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geography.nngla_unresolved_territorial_residual (
    residual_id text PRIMARY KEY CHECK (residual_id LIKE 'territorial-residual:nngla:%'),
    parent_administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    geometry geometry(Geometry,4326) NOT NULL,
    area_m2 double precision NOT NULL CHECK (area_m2 >= 0),
    adjacent_subject_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    originating_target_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_fingerprint text NOT NULL CHECK (source_fingerprint ~ '^[0-9a-f]{64}$'),
    runtime_fingerprint text NOT NULL CHECK (runtime_fingerprint ~ '^[0-9a-f]{64}$'),
    precision_policy_id text NOT NULL,
    reason text NOT NULL,
    affects_feature_boundary boolean NOT NULL DEFAULT false,
    review_status text NOT NULL CHECK (review_status IN ('REVIEW_DEFERRED','RESOLVED','SUPERSEDED')),
    visibility text NOT NULL CHECK (visibility='INTERNAL'),
    publication_status text NOT NULL CHECK (publication_status='NOT_PUBLISHED'),
    supersedes_residual_id text REFERENCES geography.nngla_unresolved_territorial_residual(residual_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (NOT ST_IsEmpty(geometry) AND ST_IsValid(geometry) AND ST_SRID(geometry)=4326)
);
CREATE INDEX ix_nngla_residual_parent_review
ON geography.nngla_unresolved_territorial_residual(parent_administrative_area_id,review_status);

CREATE TABLE geography.nngla_administrative_fabric_completeness (
    completeness_id text PRIMARY KEY CHECK (completeness_id LIKE 'fabric-completeness:nngla:%'),
    parent_administrative_area_id text NOT NULL REFERENCES geography.nngla_administrative_area(administrative_area_id) ON DELETE RESTRICT,
    child_type_code text NOT NULL,
    completeness_status text NOT NULL CHECK (completeness_status IN ('NOT_ASSESSED','PARTIAL','COMPLETE')),
    expected_child_count integer NOT NULL CHECK (expected_child_count >= 0),
    qualified_child_count integer NOT NULL CHECK (qualified_child_count >= 0),
    published_child_count integer NOT NULL CHECK (published_child_count >= 0),
    gap_m2 double precision NOT NULL CHECK (gap_m2 >= 0),
    positive_overlap_m2 double precision NOT NULL CHECK (positive_overlap_m2 >= 0),
    evidence_sha256 text NOT NULL CHECK (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    assessed_at timestamptz NOT NULL DEFAULT now(),
    CHECK (qualified_child_count <= expected_child_count AND published_child_count <= qualified_child_count),
    CHECK (completeness_status <> 'COMPLETE' OR (qualified_child_count=expected_child_count AND gap_m2=0 AND positive_overlap_m2=0))
);
CREATE INDEX ix_nngla_fabric_completeness_parent
ON geography.nngla_administrative_fabric_completeness(parent_administrative_area_id,child_type_code,runtime_mode,assessed_at DESC);

COMMIT;
