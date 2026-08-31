BEGIN;
DROP VIEW IF EXISTS geography.nngla_municipality_public_read_v1;
DROP TABLE IF EXISTS geography.nngla_municipality_publication;
DROP TABLE IF EXISTS geography.nngla_municipality_partition_qualification;
DROP TABLE IF EXISTS geography.nngla_municipality_geometry_record;
COMMIT;
