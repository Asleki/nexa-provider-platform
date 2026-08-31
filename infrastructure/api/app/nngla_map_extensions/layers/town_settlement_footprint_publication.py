"""P006.7.11.15.9 TOWN extension, corrected by sequence 29."""
from infrastructure.database.read.nngla_town_public_map import (
    PostgreSQLTownPublicMapRepository,
    TownAugmentedNNGLANationalMapRepository,
)
from infrastructure.api.services.nngla_town_map_read_service import (
    PostgreSQLTownAugmentedNNGLAMapReadService,
)


def compose(context):
    # TOWN has exactly one authority dependency here: published MUNICIPALITY.
    # CITY_DISTRICT is deliberately not a prerequisite.
    if context.resources.get("municipality_public_map_repository") is None:
        raise RuntimeError("TOWN extension requires the MUNICIPALITY map repository")
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
        context.map_read_service,
        town_repository,
    )
    return context.with_layer(
        map_repository=repository,
        map_read_service=service,
        resources={
            "town_public_map_repository": town_repository,
        },
    )
