import json
from pathlib import Path

import pytest

from infrastructure.geography.authoring import BoundaryAuthoringError, validate_authoring_contract

ROOT = Path(__file__).parents[4]
CONTRACT = ROOT / "data/novegeo/geography/world-boundary/contracts/sovereign-boundary-authoring-v001.json"


def test_high_resolution_authoring_contract_is_explicit_and_future_safe():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    validate_authoring_contract(contract)
    assert contract["applicationAxisOrder"] == ["longitude", "latitude"]
    assert contract["normalizedGeometryType"] == "MultiPolygon"
    assert contract["spatialPolicy"]["equatorCrossingExpected"] is True
    assert contract["spatialPolicy"]["antimeridianCrossingAllowed"] is False
    assert contract["authoringPolicy"]["artificialVertexDensificationForbidden"] is True
    assert contract["authoringPolicy"]["meaninglessRandomJitterForbidden"] is True


def test_authoring_contract_rejects_axis_order_reversal():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["applicationAxisOrder"] = ["latitude", "longitude"]
    with pytest.raises(BoundaryAuthoringError, match="axis order"):
        validate_authoring_contract(contract)
