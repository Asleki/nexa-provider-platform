"""Read/write the reserved M009.10 sex-usage metadata namespace."""
from __future__ import annotations
from collections.abc import Mapping
from .name_metadata import NameMetadata
from .name_sex_usage import NameSexUsage
from .name_sex_usage_errors import NameSexUsageMetadataError
_NAMESPACE="name_usage"; _KEY="sex_usage"; _VERSION_KEY="schema_version"; _VERSION=1

def read_name_sex_usage(metadata:NameMetadata)->NameSexUsage:
    if not isinstance(metadata,NameMetadata): raise TypeError("metadata must be NameMetadata.")
    section=metadata.attributes.get(_NAMESPACE)
    if section is None: return NameSexUsage.UNSPECIFIED
    if not isinstance(section,Mapping): raise NameSexUsageMetadataError("name_usage metadata must be a mapping.")
    version=section.get(_VERSION_KEY,_VERSION)
    if version!=_VERSION: raise NameSexUsageMetadataError("unsupported name_usage metadata schema_version.")
    try: return NameSexUsage.parse(section.get(_KEY,NameSexUsage.UNSPECIFIED.value))
    except (TypeError,ValueError) as exc: raise NameSexUsageMetadataError(str(exc)) from exc

def with_name_sex_usage(metadata:NameMetadata,usage:NameSexUsage|str)->NameMetadata:
    if not isinstance(metadata,NameMetadata): raise TypeError("metadata must be NameMetadata.")
    parsed=NameSexUsage.parse(usage)
    attrs={k:v for k,v in metadata.to_dict()["attributes"].items()}
    existing=attrs.get(_NAMESPACE,{})
    if existing is not None and not isinstance(existing,dict): raise NameSexUsageMetadataError("name_usage metadata must be a mapping.")
    section=dict(existing or {}); section[_VERSION_KEY]=_VERSION; section[_KEY]=parsed.value; attrs[_NAMESPACE]=section
    data=metadata.to_dict(); data["attributes"]=attrs
    return NameMetadata.from_dict(data)
__all__=["read_name_sex_usage","with_name_sex_usage"]
