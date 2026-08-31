import pytest

from infrastructure.api.app.nngla_map_extensions.contracts import NNGLAMapExtensionContext
from infrastructure.api.app.nngla_map_extensions.layers.municipality_spatial_publication import (
    compose as compose_municipality,
)
from infrastructure.api.app.nngla_map_extensions.layers.city_district_spatial_publication import (
    compose as compose_district,
)
from infrastructure.api.app.nngla_map_extensions.layers.town_settlement_footprint_publication import (
    compose as compose_town,
)


class _Repo:
    runtime_mode = "simulation"


class _Service:
    def __init__(self, repository):
        self.repository = repository

    def list_features(self, **kwargs):
        return {"items": [], "families": [], "bounds": {}, "readRuntime": "simulation"}

    def get_subject(self, subject_id):
        return None


class _ResourceRepository:
    runtime_mode = "simulation"


def _base_context():
    repo = _Repo()
    return NNGLAMapExtensionContext(
        pool=object(),
        runtime_mode="simulation",
        map_repository=repo,
        map_read_service=_Service(repo),
        resources={
            "region_public_map_repository": _ResourceRepository(),
            "city_public_map_repository": _ResourceRepository(),
        },
    )


def test_city_district_requires_city_but_not_municipality():
    result = compose_district(_base_context())
    assert "city_district_public_map_repository" in result.resources
    assert "municipality_public_map_repository" not in result.resources
    assert result.resources["city_public_map_repository"] is not None
    assert result.map_read_service.repository is result.map_repository


def test_city_district_fails_closed_without_city_authority_resource():
    repo = _Repo()
    context = NNGLAMapExtensionContext(
        pool=object(), runtime_mode="simulation", map_repository=repo,
        map_read_service=_Service(repo), resources={}
    )
    with pytest.raises(RuntimeError, match="CITY"):
        compose_district(context)


def test_town_requires_municipality_but_not_city_district():
    municipality = compose_municipality(_base_context())
    result = compose_town(municipality)
    assert "municipality_public_map_repository" in result.resources
    assert "town_public_map_repository" in result.resources
    assert "city_district_public_map_repository" not in result.resources
    assert result.map_read_service.repository is result.map_repository


def test_town_fails_closed_without_municipality_authority_resource():
    with pytest.raises(RuntimeError, match="MUNICIPALITY"):
        compose_town(_base_context())
