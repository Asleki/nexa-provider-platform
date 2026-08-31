from infrastructure.database.read.nngla_town_public_map import (
    TOWN_CLASSIFICATION_CODE,
    TOWN_FAMILY,
    TOWN_PUBLIC_VIEW,
    PostgreSQLTownPublicMapRepository,
    TownAugmentedNNGLANationalMapRepository,
)


def test_town_public_map_adapter_is_governed_national_map_layer():
    assert TOWN_PUBLIC_VIEW == "geography.nngla_town_public_read_v2"
    assert TOWN_FAMILY == "PLACE"
    assert TOWN_CLASSIFICATION_CODE == "TOWN"
    assert PostgreSQLTownPublicMapRepository
    assert TownAugmentedNNGLANationalMapRepository
