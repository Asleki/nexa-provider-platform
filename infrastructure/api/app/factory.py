from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from infrastructure.api.config import InfrastructureSettings
from infrastructure.api.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from infrastructure.api.routers import geography_router, health_router, publication_router
from infrastructure.api.routers.nngla import router as nngla_router
from infrastructure.api.services.publication_service import build_default_publication_service
from infrastructure.api.services.nngla_read_service import build_default_nngla_read_service
from infrastructure.database.runtime.pool import DatabaseUnavailable
from infrastructure.database.read.nngla import NNGLAReadAuthorityError
from infrastructure.database.read.world_boundary import WorldBoundaryAuthorityError
from infrastructure.geography import build_default_world_geometry_service
from .state import ApplicationState


def create_application(
    settings: InfrastructureSettings | None = None,
    publication_service=None,
    world_geometry_service=None,
    nngla_read_service=None,
    database_pool=None,
) -> FastAPI:
    settings = settings or InfrastructureSettings()
    state = ApplicationState()

    @asynccontextmanager
    async def lifespan(app):
        state.start()
        if database_pool is not None:
            try:
                database_pool.open()
                state.database_ready = bool(database_pool.readiness())
            except DatabaseUnavailable:
                state.database_ready = False
        try:
            yield
        finally:
            state.database_ready = False
            if database_pool is not None:
                database_pool.close()
            state.stop()

    app = FastAPI(
        title=settings.application_name,
        version=settings.application_version,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.infrastructure_state = state
    app.state.database_pool = database_pool
    app.state.publication_service = publication_service or build_default_publication_service()
    app.state.world_geometry_service = world_geometry_service or build_default_world_geometry_service()
    app.state.nngla_read_service = nngla_read_service or build_default_nngla_read_service()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_methods=["GET"],
            allow_headers=["if-none-match", "x-correlation-id"],
        )
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(publication_router, prefix=settings.api_prefix)
    app.include_router(geography_router, prefix=settings.api_prefix)
    app.include_router(nngla_router, prefix=settings.api_prefix)

    async def database_unavailable(request: Request, exc: Exception):
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "AUTHORITY_READ_UNAVAILABLE",
                    "message": "The governed database read authority is temporarily unavailable",
                    "correlationId": getattr(request.state, "correlation_id", None),
                }
            },
        )

    app.add_exception_handler(DatabaseUnavailable, database_unavailable)
    app.add_exception_handler(NNGLAReadAuthorityError, database_unavailable)
    app.add_exception_handler(WorldBoundaryAuthorityError, database_unavailable)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "correlationId": getattr(request.state, "correlation_id", None),
                }
            },
        )

    return app
