import pytest

from registries.country.locale_currency_boundary import CurrencyReferenceBoundary, LocaleReferenceBoundary


def test_p006_7_1_5_locale_boundary_references_only_governed_temporal_dimensions():
    locale = LocaleReferenceBoundary(
        timezone_code="Africa/NoveGeo",
        calendar_code="GREGORIAN",
        date_time_policy_id="dtpolicy:novegeo:v1",
    )
    assert locale.timezone_code == "Africa/NoveGeo"
    assert locale.calendar_code.value == "GREGORIAN"
    assert not hasattr(locale, "default_language")
    assert not hasattr(locale, "decimal_separator")


def test_p006_7_1_5_ngc_is_reference_not_monetary_engine():
    currency = CurrencyReferenceBoundary("NGC", "₦G", "country:novegeo")
    assert currency.currency_code == "NGC"
    assert currency.currency_symbol == "₦G"
    assert currency.country_id == "country:novegeo"
    assert not hasattr(currency, "exchange_rate")
    assert not hasattr(currency, "balance")
    assert not hasattr(currency, "minor_unit")


def test_p006_7_1_5_currency_code_is_stable_three_letter_reference():
    with pytest.raises(ValueError):
        CurrencyReferenceBoundary("NG", "₦G", "country:novegeo")
