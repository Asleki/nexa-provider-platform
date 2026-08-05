from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from infrastructure.api.config import InfrastructureSettings
from infrastructure.api.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from infrastructure.api.routers import health_router, publication_router
from infrastructure.api.services.publication_service import build_default_publication_service
from .state import ApplicationState

def create_application(settings:InfrastructureSettings|None=None, publication_service=None)->FastAPI:
    settings=settings or InfrastructureSettings()
    state=ApplicationState()
    @asynccontextmanager
    async def lifespan(app):
        state.start(); yield; state.stop()
    app=FastAPI(title=settings.application_name,version=settings.application_version,docs_url="/docs" if settings.docs_enabled else None,redoc_url=None,lifespan=lifespan)
    app.state.infrastructure_state=state
    app.state.publication_service=publication_service or build_default_publication_service()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=list(settings.trusted_hosts))
    if settings.allowed_origins: app.add_middleware(CORSMiddleware,allow_origins=list(settings.allowed_origins),allow_methods=["GET"],allow_headers=["if-none-match","x-correlation-id"])
    app.include_router(health_router,prefix=settings.api_prefix)
    app.include_router(publication_router,prefix=settings.api_prefix)
    @app.exception_handler(Exception)
    async def unhandled(request:Request, exc:Exception):
        return JSONResponse(status_code=500,content={"error":{"code":"INTERNAL_ERROR","message":"An internal error occurred","correlationId":getattr(request.state,"correlation_id",None)}})
    return app
