BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_reserve_parcel_reference(text,text,text,text);
DROP TABLE IF EXISTS geography.nngla_parcel_reference_reservation;
DROP TABLE IF EXISTS geography.nngla_parcel_reference_series;
COMMIT;
