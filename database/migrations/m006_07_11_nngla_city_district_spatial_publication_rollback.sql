BEGIN;
DROP VIEW IF EXISTS geography.nngla_city_district_public_read_v1;
DROP VIEW IF EXISTS geography.nngla_city_district_partition_exact_read_v1;
DROP TABLE IF EXISTS geography.nngla_city_district_publication;
DROP TABLE IF EXISTS geography.nngla_city_district_partition_qualification;
DROP TABLE IF EXISTS geography.nngla_city_district_geometry_record;
COMMIT;
