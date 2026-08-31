from infrastructure.api.app.nngla_map_extensions.contracts import NNGLAMapExtensionContext
from infrastructure.api.app.nngla_map_extensions.layers.municipality_spatial_publication import (
    compose as compose_municipality,
)
from infrastructure.api.app.nngla_map_extensions.layers.city_district_spatial_publication import (
    compose as compose_city_district,
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


def test_city_district_compose_wraps_municipality_context_without_replacing_authority():
    municipality = compose_municipality(_base_context())
    result = compose_city_district(municipality)

    assert result.pool is municipality.pool
    assert result.runtime_mode == municipality.runtime_mode
    assert result.map_repository is not municipality.map_repository
    assert result.map_read_service.repository is result.map_repository
    assert "municipality_public_map_repository" in result.resources
    assert "city_district_public_map_repository" in result.resources
    assert result.resources["region_public_map_repository"] is municipality.resources[
        "region_public_map_repository"
    ]
    assert result.resources["city_public_map_repository"] is municipality.resources[
        "city_public_map_repository"
    ]
