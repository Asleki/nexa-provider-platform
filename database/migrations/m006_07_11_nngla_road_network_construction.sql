BEGIN;
-- P006.7.11.12 additive road-network topology. Locked road/segment tables are not rewritten.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_road_network_node (
    node_id text PRIMARY KEY CHECK (node_id LIKE 'roadnode:nngla:%'),
    longitude double precision NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    latitude double precision NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    place_id text CHECK (place_id IS NULL OR place_id ~ '^NG-PLC-[0-9]{6}$'),
    region_code text NOT NULL,
    node_role text NOT NULL CHECK (node_role IN ('ENDPOINT','JUNCTION')),
    runtime_effect_scope text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE geography.nngla_road_segment_topology (
    road_segment_id text PRIMARY KEY REFERENCES geography.nngla_road_segment(road_segment_id),
    start_node_id text NOT NULL REFERENCES geography.nngla_road_network_node(node_id),
    end_node_id text NOT NULL REFERENCES geography.nngla_road_network_node(node_id),
    length_m double precision NOT NULL CHECK (length_m > 0),
    geometry_reservation_key text NOT NULL,
    qualification_status text NOT NULL,
    runtime_effect_scope text NOT NULL,
    CHECK (start_node_id <> end_node_id)
);

CREATE TABLE geography.nngla_road_network_connection (
    connection_id text PRIMARY KEY CHECK (connection_id LIKE 'roadconn:nngla:%'),
    node_id text NOT NULL REFERENCES geography.nngla_road_network_node(node_id),
    road_segment_id text NOT NULL REFERENCES geography.nngla_road_segment(road_segment_id),
    road_id text NOT NULL CHECK (road_id ~ '^NG-RD-[0-9]{6}$'),
    endpoint_role text NOT NULL CHECK (endpoint_role IN ('START','END')),
    runtime_effect_scope text NOT NULL,
    UNIQUE(node_id, road_segment_id)
);

CREATE TABLE geography.nngla_spatial_relationship_evidence (
    relationship_id text PRIMARY KEY,
    subject_type text NOT NULL,
    subject_id text NOT NULL,
    relationship_type text NOT NULL,
    object_type text NOT NULL,
    object_id text NOT NULL,
    longitude double precision CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    latitude double precision CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    evidence_basis text NOT NULL,
    qualification_status text NOT NULL,
    runtime_effect_scope text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(subject_id, relationship_type, object_id, runtime_effect_scope)
);

CREATE INDEX ix_nngla_road_network_node_place ON geography.nngla_road_network_node(place_id,region_code);
CREATE INDEX ix_nngla_road_network_connection_road ON geography.nngla_road_network_connection(road_id,node_id);
CREATE INDEX ix_nngla_spatial_relationship_subject ON geography.nngla_spatial_relationship_evidence(subject_type,subject_id,relationship_type);
COMMIT;
