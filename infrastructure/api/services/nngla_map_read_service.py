"""P006.7.11.15.2 map-oriented NNGLA service."""
from __future__ import annotations
import base64
from hashlib import sha256
import json
from infrastructure.database.read.nngla_national_map import MAP_FAMILIES, MapBounds, NNGLAMapReadAuthorityError

def _checksum(payload: object) -> str:
    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()

def _encode_cursor(key: tuple[str,str] | None) -> str | None:
    if key is None: return None
    return base64.urlsafe_b64encode(f"{key[0]}\n{key[1]}".encode()).decode().rstrip("=")

def _decode_cursor(value: str | None) -> tuple[str,str] | None:
    if not value: return None
    try:
        raw=value + "=" * (-len(value)%4)
        family,subject=base64.urlsafe_b64decode(raw.encode()).decode().split("\n",1)
    except Exception as exc:
        raise ValueError("invalid map cursor") from exc
    if family not in MAP_FAMILIES or not subject: raise ValueError("invalid map cursor")
    return family,subject

def _feature(item) -> dict[str,object]:
    return {
        "subjectId":item.subject_id,"family":item.family,"displayName":item.display_name,
        "publicationReference":item.publication_reference,"publicEligible":True,"mapRenderable":True,
        "geometryId":item.geometry_id,"geometryVersion":item.geometry_version,"geometryRole":item.geometry_role,
        "geometryType":item.geometry_type,"crsCode":item.crs_code,"geometry":item.geometry,
        "runtimeEffectScope":item.runtime_effect_scope,"classificationScheme":item.classification_scheme,
        "classificationCode":item.classification_code,"readModelVersion":item.read_model_version,
    }

class UnavailableNNGLAMapReadService:
    def _raise(self): raise NNGLAMapReadAuthorityError("live PostgreSQL map read authority is not configured")
    def list_features(self, **_kwargs): self._raise()
    def get_subject(self, _subject_id): self._raise()

def build_default_nngla_map_read_service(): return UnavailableNNGLAMapReadService()

class PostgreSQLNNGLAMapReadService:
    def __init__(self, repository) -> None:
        if repository is None: raise TypeError("repository is required")
        self.repository=repository
    def list_features(self, *, min_longitude:float,min_latitude:float,max_longitude:float,max_latitude:float,families=None,limit:int=500,cursor:str|None=None) -> dict[str,object]:
        selected=tuple(dict.fromkeys(str(f).strip().upper() for f in (families or MAP_FAMILIES)))
        if not selected or any(f not in MAP_FAMILIES for f in selected): raise ValueError("unsupported map family")
        bounds=MapBounds(min_longitude,min_latitude,max_longitude,max_latitude)
        page=self.repository.list_features(bounds=bounds,families=selected,limit=limit,after=_decode_cursor(cursor))
        items=[_feature(item) for item in page.items]
        semantic={"runtime":self.repository.runtime_mode,"bounds":[min_longitude,min_latitude,max_longitude,max_latitude],"families":list(selected),"items":items,"nextCursor":_encode_cursor(page.last_key),"readModelVersion":page.read_model_version}
        return {
            "authorityId":"authority:nngla","countryId":"country:novegeo","readRuntime":self.repository.runtime_mode,
            "mapReadModelVersion":page.read_model_version,"bounds":{"minLongitude":min_longitude,"minLatitude":min_latitude,"maxLongitude":max_longitude,"maxLatitude":max_latitude},
            "families":list(selected),"items":items,"count":len(items),"nextCursor":_encode_cursor(page.last_key),
            "privacyBoundary":"PUBLIC_READ_MODELS_ONLY","databaseAuthority":"SERVER_SIDE_ONLY","semanticChecksum":_checksum(semantic),
        }
    def get_subject(self, subject_id:str) -> dict[str,object] | None:
        item=self.repository.get_subject(subject_id)
        if item is None: return None
        feature=_feature(item)
        semantic={"runtime":self.repository.runtime_mode,"item":feature}
        return {"authorityId":"authority:nngla","countryId":"country:novegeo","readRuntime":self.repository.runtime_mode,"item":feature,"semanticChecksum":_checksum(semantic)}

__all__=["PostgreSQLNNGLAMapReadService","UnavailableNNGLAMapReadService","build_default_nngla_map_read_service"]
