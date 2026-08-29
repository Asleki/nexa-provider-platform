"""Environment-driven composition for live PostgreSQL read authority.

The historical ``create_application`` composition remains the default when
``INFRA_READ_AUTHORITY`` is absent or ``source``.  Live deployments opt in to
PostgreSQL explicitly, preserving locked P006.7.9 test behavior.
"""
from __future__ import annotations

import os
from typing import Mapping

from infrastructure.api.config import InfrastructureSettings
from infrastructure.api.services.nngla_postgresql_read_service import PostgreSQLNNGLAReadService
from infrastructure.api.services.nngla_map_read_service import PostgreSQLNNGLAMapReadService
from infrastructure.api.services.nngla_region_map_read_service import PostgreSQLRegionAugmentedNNGLAMapReadService
from infrastructure.database import DatabaseRuntimeSettings, PostgreSQLPool
from infrastructure.database.read import PostgreSQLNNGLAReadRepository, PostgreSQLWorldBoundaryRepository
from infrastructure.database.read.nngla_national_map import PostgreSQLNNGLANationalMapRepository
from infrastructure.database.read.nngla_region_public_map import (
    PostgreSQLRegionPublicMapRepository,
    RegionAugmentedNNGLANationalMapRepository,
)
from infrastructure.geography.service import WorldGeometryService

from .factory import create_application


READ_AUTHORITY_SOURCE = "source"
READ_AUTHORITY_POSTGRESQL = "postgresql"


def create_application_from_environment(env: Mapping[str, str] | None = None):
    values = os.environ if env is None else env
    defaults = InfrastructureSettings()
    split = lambda key: tuple(v.strip() for v in values.get(key, "").split(",") if v.strip())
    settings = InfrastructureSettings(
        application_name=values.get("INFRA_APPLICATION_NAME", defaults.application_name),
        application_version=values.get("INFRA_APPLICATION_VERSION", defaults.application_version),
        environment_name=values.get("INFRA_ENVIRONMENT", defaults.environment_name),
        api_prefix=values.get("INFRA_API_PREFIX", defaults.api_prefix),
        allowed_origins=split("INFRA_ALLOWED_ORIGINS"),
        trusted_hosts=split("INFRA_TRUSTED_HOSTS") or defaults.trusted_hosts,
        docs_enabled=values.get("INFRA_DOCS_ENABLED", "true").lower() in {"1", "true", "yes"},
    )
    authority = str(values.get("INFRA_READ_AUTHORITY", READ_AUTHORITY_SOURCE)).strip().lower()

    if authority == READ_AUTHORITY_SOURCE:
        return create_application(settings)
    if authority != READ_AUTHORITY_POSTGRESQL:
        raise ValueError("INFRA_READ_AUTHORITY must be 'source' or 'postgresql'")

    runtime_mode = str(values.get("INFRA_NNGLA_READ_RUNTIME", "simulation")).strip().lower()
    database_settings = DatabaseRuntimeSettings.from_mapping(values)
    pool = PostgreSQLPool(database_settings)
    world_geometry_service = WorldGeometryService(PostgreSQLWorldBoundaryRepository(pool))
    nngla_read_service = PostgreSQLNNGLAReadService(
        PostgreSQLNNGLAReadRepository(pool, runtime_mode=runtime_mode)
    )
    base_nngla_map_repository = PostgreSQLNNGLANationalMapRepository(pool, runtime_mode=runtime_mode)
    region_public_map_repository = PostgreSQLRegionPublicMapRepository(pool, runtime_mode=runtime_mode)
    nngla_map_repository = RegionAugmentedNNGLANationalMapRepository(
        base_nngla_map_repository,
        region_public_map_repository,
    )
    nngla_map_read_service = PostgreSQLRegionAugmentedNNGLAMapReadService(
        nngla_map_repository,
        region_public_map_repository,
    )
    return create_application(
        settings,
        world_geometry_service=world_geometry_service,
        nngla_read_service=nngla_read_service,
        nngla_map_read_service=nngla_map_read_service,
        database_pool=pool,
    )


__all__ = [
    "READ_AUTHORITY_POSTGRESQL",
    "READ_AUTHORITY_SOURCE",
    "create_application_from_environment",
]
