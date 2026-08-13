from pathlib import Path

from registries.country.qualification import qualify_bundle13a_source
from registries.country.source import read_country_profile

ROOT = Path(__file__).parents[4]
PROFILE = ROOT / "data/novegeo/country/source/novegeo_country_profile.csv"


def test_bundle13a_country_source_is_real_governed_data_not_template_or_runtime_storage():
    source = read_country_profile(PROFILE)
    assert source.identity.country_id == "country:novegeo"
    assert source.alpha2.code_value == "NV"
    assert source.alpha3.code_value == "NVG"
    assert source.active_boundary_version == 2

    provenance = (ROOT / "data/novegeo/country/provenance/novegeo_country_profile_source.json").read_text(encoding="utf-8")
    assert '"operationalAuthority": false' in provenance
    assert '"runtimeCsvConsumptionAllowed": false' in provenance
    assert "PostgreSQL" in provenance


def test_bundle13a_qualification_joins_country_source_to_existing_governed_v002_boundary():
    receipt = qualify_bundle13a_source(ROOT)
    assert receipt.status == "PASSED"
    assert receipt.boundary.boundary_id == "boundary:novegeo:sovereign"
    assert receipt.boundary.boundary_version == 2
    assert receipt.boundary.runtime_mode == "shared_reference"
    assert receipt.boundary.coordinate_reference_id == "crs:novegeo:geographic"
    assert len(receipt.source_sha256) == 64
    assert "CSV_RUNTIME_AUTHORITY_PROHIBITED" in receipt.findings


def test_bundle13a_does_not_modify_or_duplicate_locked_world_boundary_source():
    country_dir = ROOT / "data/novegeo/country"
    assert not list(country_dir.rglob("*.geojson"))
    locked = ROOT / "data/novegeo/geography/world-boundary/candidate/novegeo_world_boundary_v002.geojson"
    assert locked.is_file()
