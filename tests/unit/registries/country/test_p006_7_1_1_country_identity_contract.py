from datetime import date
import pytest

from registries.country.contracts import CountryIdentity, CountryLifecycleStatus, SovereigntyStatus


def test_p006_7_1_1_country_identity_is_stable_and_not_a_country_code():
    country = CountryIdentity(
        country_id="country:novegeo",
        official_name="NoveGeo",
        short_name="NoveGeo",
        sovereignty_status="SIMULATED_SOVEREIGN",
        status="ACTIVE",
        effective_from=date(2026, 8, 12),
        source_reference="NNGLA Phase A + governed NoveGeo geography",
    )
    assert country.country_id == "country:novegeo"
    assert country.country_id not in {"NV", "NVG"}
    assert country.sovereignty_status is SovereigntyStatus.SIMULATED_SOVEREIGN
    assert country.status is CountryLifecycleStatus.ACTIVE


def test_p006_7_1_1_country_identity_rejects_unnamespaced_or_invalid_lifecycle():
    with pytest.raises(ValueError):
        CountryIdentity("NV", "NoveGeo", "NoveGeo", "SIMULATED_SOVEREIGN", "ACTIVE", date(2026, 8, 12))
    with pytest.raises(ValueError):
        CountryIdentity("country:novegeo", "NoveGeo", "NoveGeo", "SIMULATED_SOVEREIGN", "ACTIVE", date(2026, 8, 13), date(2026, 8, 12))
