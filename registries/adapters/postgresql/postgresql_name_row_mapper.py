"""Map PostgreSQL rows to locked M009.1 CanonicalName records."""
from __future__ import annotations
import json
from collections.abc import Mapping,Sequence
from registries.names import CanonicalName,NameMetadata
class PostgreSQLNameRowMapper:
    COLUMNS=("name_id","canonical_value","name_kind","status","runtime_mode","schema_version","created_at","source_reference","language_refs","country_refs","region_refs","culture_refs","script_code","attributes")
    @classmethod
    def to_record(cls,row:Mapping[str,object]|Sequence[object])->CanonicalName:
        data=dict(row) if isinstance(row,Mapping) else dict(zip(cls.COLUMNS,row,strict=True))
        def obj(value,default):
            if value is None:return default
            if isinstance(value,str):return json.loads(value)
            return value
        metadata=NameMetadata(status=data["status"],runtime_mode=data["runtime_mode"],schema_version=data["schema_version"],created_at=data["created_at"],source_reference=data.get("source_reference"),language_refs=tuple(obj(data.get("language_refs"),[])),country_refs=tuple(obj(data.get("country_refs"),[])),region_refs=tuple(obj(data.get("region_refs"),[])),culture_refs=tuple(obj(data.get("culture_refs"),[])),script_code=data.get("script_code"),attributes=obj(data.get("attributes"),{}))
        return CanonicalName(str(data["name_id"]),str(data["canonical_value"]),data["name_kind"],metadata)
    @classmethod
    def parameters(cls,record:CanonicalName)->tuple[object,...]:
        if not isinstance(record,CanonicalName): raise TypeError("record must be CanonicalName.")
        m=record.metadata
        return (record.name_id,record.canonical_value,record.search_value,record.name_kind.value,m.status.value,m.runtime_mode,m.schema_version,m.created_at,m.source_reference,json.dumps(list(m.language_refs)),json.dumps(list(m.country_refs)),json.dumps(list(m.region_refs)),json.dumps(list(m.culture_refs)),m.script_code,json.dumps(m.to_dict()["attributes"],sort_keys=True))
__all__=["PostgreSQLNameRowMapper"]
