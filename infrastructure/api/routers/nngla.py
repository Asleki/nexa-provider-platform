"""P006.7.9 read-only NNGLA public registry endpoints."""
from fastapi import APIRouter, Header, HTTPException, Request, Response

router = APIRouter(prefix="/nngla", tags=["nngla"])

_FAMILY_PATHS = {
    "places": "PLACE",
    "features": "GEOGRAPHIC_FEATURE",
    "administrative-areas": "ADMINISTRATIVE_AREA",
    "roads": "ROAD",
    "addresses": "ADDRESS",
    "parcels": "PARCEL",
}


def _etag(checksum: str) -> str:
    return f'"sha256:{checksum}"'


@router.get("/status")
def get_nngla_status(request: Request, response: Response, if_none_match: str | None = Header(default=None)):
    body = request.app.state.nngla_read_service.status_dict()
    etag = _etag(str(body["semanticChecksum"]))
    response.headers["etag"] = etag
    response.headers["cache-control"] = "public, max-age=60"
    if if_none_match == etag:
        response.status_code = 304
        return None
    return body


@router.get("/{family_path}")
def list_public_family(family_path: str, request: Request, response: Response, if_none_match: str | None = Header(default=None)):
    family = _FAMILY_PATHS.get(family_path)
    if family is None:
        raise HTTPException(status_code=404, detail={"code": "NNGLA_READ_FAMILY_NOT_FOUND", "message": "Unsupported NNGLA public read family"})
    body = request.app.state.nngla_read_service.list_public(family)
    etag = _etag(str(body["semanticChecksum"]))
    response.headers["etag"] = etag
    response.headers["cache-control"] = "public, max-age=60"
    if if_none_match == etag:
        response.status_code = 304
        return None
    return body
