from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from registries.core import (
    DEFAULT_NUMBERING_STRATEGY_VERSION, NumberingMode,
    NumberingStrategy, NumberingStrategyError,
)


def _model(**overrides):
    values = dict(strategy_id=" strat-1 ", registry_id=" reg.birth ",
                  namespace_id=" ns.civil ", identifier_id=" id.birth ",
                  strategy_code=" birth_seq ", strategy_name=" Birth Sequence ",
                  mode="sequential", prefix=" BR- ", suffix=" ",
                  padding_length=8, version=1, metadata={" owner ": "civil"})
    values.update(overrides)
    return NumberingStrategy(**values)


def test_valid_model_and_backward_compatible_properties():
    model = _model()
    assert model.strategy_code == "BIRTH_SEQ"
    assert model.mode is NumberingMode.SEQUENTIAL
    assert model.prefix == "BR-" and model.suffix is None
    assert model.padded
    assert model.identity == ("strat-1", "BIRTH_SEQ")
    assert model.ownership == ("reg.birth", "ns.civil", "id.birth")
    assert model.qualified_code == "reg.birth:ns.civil:BIRTH_SEQ"
    assert model.version == DEFAULT_NUMBERING_STRATEGY_VERSION


def test_enum_and_numeric_guards():
    with pytest.raises(NumberingStrategyError, match="Unsupported numbering mode"):
        _model(mode="hash")
    with pytest.raises(TypeError, match="padding_length"):
        _model(padding_length=True)
    with pytest.raises(NumberingStrategyError, match="greater than zero"):
        _model(padding_length=0)
    with pytest.raises(TypeError, match="version must be an integer"):
        _model(version=True)
    with pytest.raises(NumberingStrategyError, match="greater than or equal"):
        _model(version=0)


def test_metadata_serialization_and_strict_mapping():
    source = {" owner ": "civil"}
    model = _model(metadata=source)
    source[" owner "] = "changed"
    assert model.metadata == {"owner": "civil"}
    assert isinstance(model.metadata, MappingProxyType)
    payload = model.to_dict()
    before = dict(payload)
    assert NumberingStrategy.from_dict(payload) == model
    assert payload == before
    with pytest.raises(TypeError, match="values must be a mapping"):
        NumberingStrategy.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        NumberingStrategy.from_dict({**payload, "unknown": True})
    with pytest.raises(FrozenInstanceError):
        model.strategy_name = "Changed"


def test_numbering_model_has_no_generation_or_sequence_state():
    forbidden = {"generate", "next", "reserve", "allocate", "current_value", "counter"}
    assert forbidden.isdisjoint(set(dir(_model())))
