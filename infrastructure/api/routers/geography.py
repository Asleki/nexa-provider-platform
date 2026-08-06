"""Read-only public geography routes for P004.1-P004.2."""
from fastapi import APIRouter, HTTPException, Request, Response

from infrastructure.geography.service import WorldGeometryNotFound

router = APIRouter(prefix="/geography", tags=["geography"])


@router.get("/world-boundary")
def get_world_boundary(request: Request, response: Response):
    try:
        publication = request.app.state.world_geometry_service.get_active()
    except WorldGeometryNotFound as exc:
        raise HTTPException(status_code=404, detail={"code": "WORLD_BOUNDARY_NOT_FOUND", "message": str(exc)}) from exc
    response.headers["etag"] = f'"sha256:{publication.content_sha256}"'
    response.headers["cache-control"] = "public, max-age=300"
    return publication.to_public_dict()


@router.get("/coordinate-reference")
def get_coordinate_reference(request: Request):
    publication = request.app.state.world_geometry_service.get_active()
    return publication.to_public_dict()["coordinateReference"]
