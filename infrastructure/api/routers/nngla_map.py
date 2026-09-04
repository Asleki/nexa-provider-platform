"""P006.7.11.15.2 / P006.7.11.15.10.1 GET-only national-map endpoints."""
from contextlib import nullcontext

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response

router = APIRouter(prefix="/nngla-map", tags=["nngla-map"])


def _etag(checksum: str) -> str:
    return f'"sha256:{checksum}"'


def _apply_cache(response: Response, body: dict[str, object], if_none_match: str | None):
    etag = _etag(str(body["semanticChecksum"]))
    response.headers["etag"] = etag
    response.headers["cache-control"] = "public, max-age=60"
    if if_none_match == etag:
        response.status_code = 304
        return None
    return body


def _map_read_scope(request: Request):
    pool = getattr(request.app.state, "database_pool", None)
    if pool is None or not hasattr(pool, "read_session"):
        return nullcontext()
    return pool.read_session()


@router.get("/features")
def list_map_features(
    request: Request,
    response: Response,
    min_longitude: float = Query(alias="minLongitude", ge=-180, le=180),
    min_latitude: float = Query(alias="minLatitude", ge=-90, le=90),
    max_longitude: float = Query(alias="maxLongitude", ge=-180, le=180),
    max_latitude: float = Query(alias="maxLatitude", ge=-90, le=90),
    family: list[str] | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    cursor: str | None = None,
    if_none_match: str | None = Header(default=None),
):
    try:
        with _map_read_scope(request):
            body = request.app.state.nngla_map_read_service.list_features(
                min_longitude=min_longitude,
                min_latitude=min_latitude,
                max_longitude=max_longitude,
                max_latitude=max_latitude,
                families=family,
                limit=limit,
                cursor=cursor,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "NNGLA_MAP_QUERY_INVALID", "message": str(exc)},
        ) from exc
    return _apply_cache(response, body, if_none_match)


@router.get("/subjects/{subject_id}")
def get_map_subject(
    subject_id: str,
    request: Request,
    response: Response,
    if_none_match: str | None = Header(default=None),
):
    with _map_read_scope(request):
        body = request.app.state.nngla_map_read_service.get_subject(subject_id)
    if body is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NNGLA_MAP_SUBJECT_NOT_FOUND",
                "message": "Published map subject not found",
            },
        )
    return _apply_cache(response, body, if_none_match)
