"""P006.7.11.15.9.2 extension registration for governed CITY_DISTRICT publication."""
from infrastructure.database.read.nngla_city_district_public_map import (
    CityDistrictAugmentedNNGLANationalMapRepository,
    PostgreSQLCityDistrictPublicMapRepository,
)
from infrastructure.api.services.nngla_city_district_map_read_service import (
    PostgreSQLCityDistrictAugmentedNNGLAMapReadService,
)


def compose(context):
    region_repository = context.resources.get("region_public_map_repository")
    city_repository = context.resources.get("city_public_map_repository")
    municipality_repository = context.resources.get("municipality_public_map_repository")
    if (
        region_repository is None
        or city_repository is None
        or municipality_repository is None
    ):
        raise RuntimeError(
            "CITY_DISTRICT extension requires locked REGION, CITY and MUNICIPALITY map repositories"
        )

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
        region_repository,
        city_repository,
        municipality_repository,
        city_district_repository,
    )
    return context.with_layer(
        map_repository=repository,
        map_read_service=service,
        resources={
            "city_district_public_map_repository": city_district_repository,
        },
    )
