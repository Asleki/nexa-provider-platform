"""P006.7.11.15.9 CITY_DISTRICT extension, corrected by sequence 29."""
from infrastructure.database.read.nngla_city_district_public_map import (
    CityDistrictAugmentedNNGLANationalMapRepository,
    PostgreSQLCityDistrictPublicMapRepository,
)
from infrastructure.api.services.nngla_city_district_map_read_service import (
    PostgreSQLCityDistrictAugmentedNNGLAMapReadService,
)


def compose(context):
    # CITY_DISTRICT has exactly one authority dependency here: the locked
    # published CITY layer. MUNICIPALITY is deliberately not a prerequisite.
    if context.resources.get("city_public_map_repository") is None:
        raise RuntimeError("CITY_DISTRICT extension requires the locked CITY map repository")
    city_district_repository = PostgreSQLCityDistrictPublicMapRepository(
        context.pool,
        runtime_mode=context.runtime_mode,
    )
    repository = CityDistrictAugmentedNNGLANationalMapRepository(
        context.map_repository,
        city_district_repository,
    )
    service = PostgreSQLCityDistrictAugmentedNNGLAMapReadService(
        repository,
        context.map_read_service,
        city_district_repository,
    )
    return context.with_layer(
        map_repository=repository,
        map_read_service=service,
        resources={
            "city_district_public_map_repository": city_district_repository,
        },
    )
