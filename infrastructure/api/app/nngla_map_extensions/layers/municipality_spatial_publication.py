"""CM1 extension registration for governed MUNICIPALITY publication."""
from infrastructure.database.read.nngla_municipality_public_map import (
    MunicipalityAugmentedNNGLANationalMapRepository,
    PostgreSQLMunicipalityPublicMapRepository,
)
from infrastructure.api.services.nngla_municipality_map_read_service import (
    PostgreSQLMunicipalityAugmentedNNGLAMapReadService,
)


def compose(context):
    region_repository = context.resources.get("region_public_map_repository")
    city_repository = context.resources.get("city_public_map_repository")
    if region_repository is None or city_repository is None:
        raise RuntimeError(
            "MUNICIPALITY extension requires locked REGION and CITY map repositories"
        )

    municipality_repository = PostgreSQLMunicipalityPublicMapRepository(
        context.pool,
        runtime_mode=context.runtime_mode,
    )
    repository = MunicipalityAugmentedNNGLANationalMapRepository(
        context.map_repository,
        municipality_repository,
    )
    service = PostgreSQLMunicipalityAugmentedNNGLAMapReadService(
        repository,
        region_repository,
        city_repository,
        municipality_repository,
    )
    return context.with_layer(
        map_repository=repository,
        map_read_service=service,
        resources={
            "municipality_public_map_repository": municipality_repository,
        },
    )
