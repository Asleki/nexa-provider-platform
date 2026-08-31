from infrastructure.database.read.nngla_city_district_public_map import (
    CITY_DISTRICT_CLASSIFICATION_CODE,
    CITY_DISTRICT_FAMILY,
    CITY_DISTRICT_PUBLIC_VIEW,
    CityDistrictAugmentedNNGLANationalMapRepository,
    PostgreSQLCityDistrictPublicMapRepository,
)


def test_city_district_public_map_adapter_is_governed_national_map_layer():
    assert CITY_DISTRICT_PUBLIC_VIEW == "geography.nngla_city_district_public_read_v1"
    assert CITY_DISTRICT_FAMILY == "ADMINISTRATIVE_AREA"
    assert CITY_DISTRICT_CLASSIFICATION_CODE == "CITY_DISTRICT"
    assert PostgreSQLCityDistrictPublicMapRepository
    assert CityDistrictAugmentedNNGLANationalMapRepository
