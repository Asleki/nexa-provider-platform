from infrastructure.api.app.nngla_map_extensions.contracts import NNGLAMapExtensionContext
from infrastructure.api.app.nngla_map_extensions.layers.municipality_spatial_publication import (
    compose as compose_municipality,
)
from infrastructure.api.app.nngla_map_extensions.layers.city_district_spatial_publication import (
    compose as compose_city_district,
)
from infrastructure.api.app.nngla_map_extensions.layers.town_settlement_footprint_publication import (
    compose as compose_town,
)


class _Repository:
    runtime_mode = "simulation"


class _Service:
    def __init__(self, repository):
        self.repository = repository


class _ResourceRepository:
    runtime_mode = "simulation"


def _base_context():
    repository = _Repository()
    return NNGLAMapExtensionContext(
        pool=object(),
        runtime_mode="simulation",
        map_repository=repository,
        map_read_service=_Service(repository),
        resources={
            "region_public_map_repository": _ResourceRepository(),
            "city_public_map_repository": _ResourceRepository(),
        },
    )


def test_town_compose_wraps_exact_municipality_city_district_chain():
    municipality = compose_municipality(_base_context())
    city_district = compose_city_district(municipality)
    result = compose_town(city_district)

    assert result.pool is city_district.pool
    assert result.runtime_mode == city_district.runtime_mode
    assert result.map_repository is not city_district.map_repository
    assert result.map_read_service.repository is result.map_repository
    assert "municipality_public_map_repository" in result.resources
    assert "city_district_public_map_repository" in result.resources
    assert "town_public_map_repository" in result.resources
