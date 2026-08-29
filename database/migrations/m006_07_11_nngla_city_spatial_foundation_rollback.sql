BEGIN;

DROP VIEW IF EXISTS geography.nngla_city_public_read_v1;
DROP TABLE IF EXISTS geography.nngla_city_publication;
DROP TABLE IF EXISTS geography.nngla_city_geometry_record;

COMMIT;
