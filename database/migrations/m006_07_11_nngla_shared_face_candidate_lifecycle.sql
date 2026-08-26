BEGIN;
-- P006.7.11.15.5 Delivery 2 — governed shared-face candidate lifecycle.
-- Candidate-only authority boundary: this migration creates no effective/legal/public geometry.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_shared_face_fabric_run (
    fabric_run_id text PRIMARY KEY CHECK (fabric_run_id LIKE 'fabric-run:nngla:%'),
    requested_root_place_id text NOT NULL CHECK (requested_root_place_id ~ '^NG-PLC-[0-9]{6}$'),
    parent_administrative_area_id text NOT NULL CHECK (parent_administrative_area_id ~ '^NG-ADM-[0-9]{6}$'),
    fabric_level text NOT NULL CHECK (fabric_level IN ('REGION_LOCAL_AREAS','CITY_DISTRICTS','MUNICIPALITY_TOWNSHIPS')),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    scope_fingerprint text NOT NULL CHECK (scope_fingerprint ~ '^[0-9a-f]{64}$'),
    input_digest text NOT NULL CHECK (input_digest ~ '^[0-9a-f]{64}$'),
    runtime_signature_digest text NOT NULL CHECK (runtime_signature_digest ~ '^[0-9a-f]{64}$'),
    edge_graph_sha256 text NOT NULL CHECK (edge_graph_sha256 ~ '^[0-9a-f]{64}$'),
    face_set_sha256 text NOT NULL CHECK (face_set_sha256 ~ '^[0-9a-f]{64}$'),
    assignment_sha256 text CHECK (assignment_sha256 IS NULL OR assignment_sha256 ~ '^[0-9a-f]{64}$'),
    qualification_sha256 text CHECK (qualification_sha256 IS NULL OR qualification_sha256 ~ '^[0-9a-f]{64}$'),
    author_actor_id text NOT NULL,
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('GOVERNANCE_REQUIRED','READY_FOR_CANDIDATE_QUALIFICATION','CANDIDATE_QUALIFIED','CANDIDATE_REJECTED','CANDIDATE_STALE','CANDIDATE_SUPERSEDED')),
    parent_candidate_id text,
    parent_candidate_geometry_sha256 text CHECK (parent_candidate_geometry_sha256 IS NULL OR parent_candidate_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    package_sha256 text NOT NULL UNIQUE CHECK (package_sha256 ~ '^[0-9a-f]{64}$'),
    package_json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((parent_candidate_id IS NULL) = (parent_candidate_geometry_sha256 IS NULL))
);

CREATE TABLE geography.nngla_shared_face_fabric_input (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    input_role text NOT NULL CHECK (input_role IN ('PARENT','EXHAUSTIVE_SIBLING','NON_EXHAUSTIVE_OVERLAY')),
    subject_id text NOT NULL CHECK (subject_id ~ '^NG-ADM-[0-9]{6}$'),
    administrative_type_code text NOT NULL,
    canonical_name text NOT NULL,
    source_candidate_id text NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    source_path_reference text NOT NULL,
    PRIMARY KEY (fabric_run_id,input_role,subject_id)
);

CREATE TABLE geography.nngla_shared_face_edge_candidate (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    edge_id text NOT NULL CHECK (edge_id LIKE 'fabric-edge:nngla:%'),
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    geometry geometry(Geometry,4326) NOT NULL,
    PRIMARY KEY (fabric_run_id,edge_id)
);

CREATE TABLE geography.nngla_shared_face_edge_lineage (
    fabric_run_id text NOT NULL,
    edge_id text NOT NULL,
    source_subject_id text NOT NULL CHECK (source_subject_id ~ '^NG-ADM-[0-9]{6}$'),
    PRIMARY KEY (fabric_run_id,edge_id,source_subject_id),
    FOREIGN KEY (fabric_run_id,edge_id) REFERENCES geography.nngla_shared_face_edge_candidate(fabric_run_id,edge_id) ON DELETE RESTRICT
);

CREATE TABLE geography.nngla_shared_face_face_candidate (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    face_id text NOT NULL CHECK (face_id LIKE 'fabric-face:nngla:%'),
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    classification text NOT NULL,
    geometry geometry(Polygon,4326) NOT NULL,
    PRIMARY KEY (fabric_run_id,face_id)
);

CREATE TABLE geography.nngla_shared_face_finding (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    defect_id text NOT NULL CHECK (defect_id LIKE 'fabric-defect:nngla:%'),
    defect_kind text NOT NULL,
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    residual_class text NOT NULL,
    requires_governed_review boolean NOT NULL,
    geometry geometry(Geometry,4326) NOT NULL,
    PRIMARY KEY (fabric_run_id,defect_id)
);

CREATE TABLE geography.nngla_shared_face_governance_decision (
    decision_id text PRIMARY KEY CHECK (decision_id LIKE 'fabric-decision:nngla:%'),
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    decision_type text NOT NULL CHECK (decision_type IN ('FACE_ASSIGNMENT','BOUNDARY_CONFLICT')),
    target_id text NOT NULL,
    target_geometry_sha256 text NOT NULL CHECK (target_geometry_sha256 ~ '^[0-9a-f]{64}$'),
    owner_subject_id text CHECK (owner_subject_id IS NULL OR owner_subject_id ~ '^NG-ADM-[0-9]{6}$'),
    decision_kind text NOT NULL,
    decision_reference text NOT NULL,
    rationale text NOT NULL,
    reviewer_actor_id text NOT NULL,
    approver_actor_id text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    supersedes_decision_id text REFERENCES geography.nngla_shared_face_governance_decision(decision_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (reviewer_actor_id <> approver_actor_id)
);

CREATE TABLE geography.nngla_shared_face_face_assignment (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    face_id text NOT NULL,
    owner_subject_id text NOT NULL CHECK (owner_subject_id ~ '^NG-ADM-[0-9]{6}$'),
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    decision_kind text NOT NULL,
    decision_reference text NOT NULL,
    PRIMARY KEY (fabric_run_id,face_id),
    FOREIGN KEY (fabric_run_id,face_id) REFERENCES geography.nngla_shared_face_face_candidate(fabric_run_id,face_id) ON DELETE RESTRICT
);

CREATE TABLE geography.nngla_shared_face_geometry_candidate (
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    candidate_id text NOT NULL CHECK (candidate_id LIKE 'fabric-candidate:nngla:%'),
    subject_id text NOT NULL CHECK (subject_id ~ '^NG-ADM-[0-9]{6}$'),
    geometry_sha256 text NOT NULL CHECK (geometry_sha256 ~ '^[0-9a-f]{64}$'),
    geometry geometry(Geometry,4326) NOT NULL,
    PRIMARY KEY (fabric_run_id,candidate_id),
    UNIQUE (fabric_run_id,subject_id)
);

CREATE TABLE geography.nngla_shared_face_qualification_decision (
    qualification_id text PRIMARY KEY CHECK (qualification_id LIKE 'fabric-qualification:nngla:%'),
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    package_sha256 text NOT NULL CHECK (package_sha256 ~ '^[0-9a-f]{64}$'),
    qualifier_actor_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('CANDIDATE_QUALIFIED','CANDIDATE_REJECTED')),
    valid_all boolean NOT NULL,
    every_child_covered_by_parent boolean NOT NULL,
    union_covered_by_parent boolean NOT NULL,
    parent_covered_by_union boolean NOT NULL,
    symmetric_difference_m2 double precision NOT NULL CHECK (symmetric_difference_m2 >= 0),
    positive_overlap_m2 double precision NOT NULL CHECK (positive_overlap_m2 >= 0),
    decision_sha256 text NOT NULL UNIQUE CHECK (decision_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geography.nngla_shared_face_candidate_receipt (
    receipt_id text PRIMARY KEY CHECK (receipt_id LIKE 'fabric-receipt:nngla:%'),
    fabric_run_id text NOT NULL REFERENCES geography.nngla_shared_face_fabric_run(fabric_run_id) ON DELETE RESTRICT,
    package_sha256 text NOT NULL CHECK (package_sha256 ~ '^[0-9a-f]{64}$'),
    receipt_kind text NOT NULL CHECK (receipt_kind IN ('RECORDED','READBACK_VERIFIED','QUALIFICATION_RECORDED')),
    actor_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_nngla_shared_face_run_root_status ON geography.nngla_shared_face_fabric_run(requested_root_place_id,lifecycle_status);
CREATE INDEX ix_nngla_shared_face_run_parent ON geography.nngla_shared_face_fabric_run(parent_administrative_area_id);
CREATE INDEX ix_nngla_shared_face_governance_run ON geography.nngla_shared_face_governance_decision(fabric_run_id,target_id);
CREATE INDEX ix_nngla_shared_face_candidate_subject ON geography.nngla_shared_face_geometry_candidate(subject_id);

-- Intentionally absent: writes/triggers/functions touching nngla_geometry_version,
-- nngla_geometry_authority_record, nngla_geometry_id_reservation,
-- nngla_geometry_supersession_link, nngla_administrative_area, publication tables.
COMMIT;
