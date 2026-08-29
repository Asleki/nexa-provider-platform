BEGIN;

DROP VIEW IF EXISTS geography.nngla_region_public_read_v1;
DROP TABLE IF EXISTS geography.nngla_region_publication;
DROP TABLE IF EXISTS geography.nngla_region_geometry_record;

COMMIT;
