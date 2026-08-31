from pathlib import Path

from infrastructure.database.read.nngla_municipality_public_map import (
    MUNICIPALITY_CLASSIFICATION_CODE,
    MUNICIPALITY_FAMILY,
    MUNICIPALITY_PUBLIC_VIEW,
)
from infrastructure.database.read.nngla_city_district_public_map import (
    CITY_DISTRICT_CLASSIFICATION_CODE,
    CITY_DISTRICT_FAMILY,
    CITY_DISTRICT_PUBLIC_VIEW,
)
from infrastructure.database.read.nngla_town_public_map import (
    TOWN_CLASSIFICATION_CODE,
    TOWN_FAMILY,
    TOWN_PUBLIC_VIEW,
)

ROOT = Path(__file__).resolve().parents[3]


def test_municipality_adapter_uses_v2_without_complete_gate():
    assert MUNICIPALITY_PUBLIC_VIEW == "geography.nngla_municipality_public_read_v2"
    assert MUNICIPALITY_FAMILY == "ADMINISTRATIVE_AREA"
    assert MUNICIPALITY_CLASSIFICATION_CODE == "MUNICIPALITY"
    s = (ROOT / "infrastructure/database/read/nngla_municipality_public_map.py").read_text()
    assert "v.partition_status='COMPLETE'" not in s


def test_city_district_adapter_uses_v2_and_accepts_partial_fabric_metadata():
    assert CITY_DISTRICT_PUBLIC_VIEW == "geography.nngla_city_district_public_read_v2"
    assert CITY_DISTRICT_FAMILY == "ADMINISTRATIVE_AREA"
    assert CITY_DISTRICT_CLASSIFICATION_CODE == "CITY_DISTRICT"
    s = (ROOT / "infrastructure/database/read/nngla_city_district_public_map.py").read_text()
    assert "WHERE v.partition_status='COMPLETE'" not in s
    assert '{"PARTIAL", "COMPLETE"}' in s


def test_town_adapter_uses_parent_authority_v2_and_place_family():
    assert TOWN_PUBLIC_VIEW == "geography.nngla_town_public_read_v2"
    assert TOWN_FAMILY == "PLACE"
    assert TOWN_CLASSIFICATION_CODE == "TOWN"
    s = (ROOT / "infrastructure/database/read/nngla_town_public_map.py").read_text()
    assert "nngla_town_public_read_v2" in s
