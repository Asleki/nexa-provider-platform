"""P006.7.11.15.9.3 extension registration for governed TOWN publication."""
from infrastructure.database.read.nngla_town_public_map import (
    PostgreSQLTownPublicMapRepository,
    TownAugmentedNNGLANationalMapRepository,
)
from infrastructure.api.services.nngla_town_map_read_service import (
    PostgreSQLTownAugmentedNNGLAMapReadService,
)


def compose(context):
    region_repository = context.resources.get("region_public_map_repository")
    city_repository = context.resources.get("city_public_map_repository")
    municipality_repository = context.resources.get("municipality_public_map_repository")
    city_district_repository = context.resources.get(
        "city_district_public_map_repository"
    )
    if (
        region_repository is None
        or city_repository is None
        or municipality_repository is None
        or city_district_repository is None
    ):
        raise RuntimeError(
            "TOWN extension requires locked REGION, CITY, MUNICIPALITY and CITY_DISTRICT map repositories"
        )

    town_repository = PostgreSQLTownPublicMapRepository(
        context.pool,
        runtime_mode=context.runtime_mode,
    )
    repository = TownAugmentedNNGLANationalMapRepository(
        context.map_repository,
        town_repository,
    )
    service = PostgreSQLTownAugmentedNNGLAMapReadService(
        repository,
        region_repository,
        city_repository,
        municipality_repository,
        city_district_repository,
        town_repository,
    )
    return context.with_layer(
        map_repository=repository,
        map_read_service=service,
        resources={
            "town_public_map_repository": town_repository,
        },
    )
