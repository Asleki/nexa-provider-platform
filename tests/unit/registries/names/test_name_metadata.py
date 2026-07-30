from datetime import datetime,timezone
from types import MappingProxyType
import pytest
from registries.names import NameMetadata,NameStatus

def test_metadata_normalizes_freezes_and_round_trips():
    m=NameMetadata(status="ACTIVE",runtime_mode=" Simulation ",created_at=datetime(2026,1,1,tzinfo=timezone.utc),language_refs=["lang:sn","lang:sn"],attributes={"source":{"rank":[1,2]}})
    assert m.status is NameStatus.ACTIVE and m.runtime_mode=="simulation"
    assert m.language_refs==("lang:sn",)
    assert isinstance(m.attributes,MappingProxyType)
    assert NameMetadata.from_dict(m.to_dict())==m

def test_metadata_rejects_unsafe_shapes():
    with pytest.raises(ValueError): NameMetadata(created_at=datetime(2026,1,1))
    with pytest.raises(TypeError): NameMetadata(attributes={1:"bad"})
    with pytest.raises(ValueError): NameMetadata(schema_version=0)
