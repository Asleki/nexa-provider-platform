from datetime import date
import pytest

from registries.country.contracts import CountryCodeAssignment, CountryCodeKind, CountryCodeScheme


def test_p006_7_1_2_nv_and_nvg_are_internal_sovereign_codes_not_country_identity():
    alpha2 = CountryCodeAssignment("country:novegeo", "ALPHA2", "NV", effective_from=date(2026, 8, 12))
    alpha3 = CountryCodeAssignment("country:novegeo", "ALPHA3", "NVG", effective_from=date(2026, 8, 12))
    assert alpha2.code_kind is CountryCodeKind.ALPHA2
    assert alpha3.code_kind is CountryCodeKind.ALPHA3
    assert alpha2.scheme is CountryCodeScheme.NOVEGEO_SOVEREIGN
    assert alpha2.external_iso_assignment is False
    assert alpha3.external_iso_assignment is False


def test_p006_7_1_2_synthetic_codes_cannot_claim_external_iso_assignment():
    with pytest.raises(ValueError, match="must not claim external ISO"):
        CountryCodeAssignment("country:novegeo", "ALPHA2", "NV", external_iso_assignment=True)
    with pytest.raises(ValueError):
        CountryCodeAssignment("country:novegeo", "ALPHA2", "NVG")
    with pytest.raises(ValueError):
        CountryCodeAssignment("country:novegeo", "ALPHA3", "N1G")
