from registries.nngla.migration_ready.catalogue import ROOT
from registries.nngla.migration_ready.empty_registers import assess_empty_registers, empty_registers_ready


def test_historical_and_operational_empty_registers_are_intentionally_ready():
    statuses = assess_empty_registers(ROOT)
    assert [row.domain_key for row in statuses] == [
        "addresses", "parcels", "titles", "state-land", "survey-control"
    ]
    assert empty_registers_ready(statuses)
    assert all(row.historical_row_count == 0 for row in statuses)
    assert all(row.operational_row_count == 0 for row in statuses)
    assert all(row.operational_contract_valid for row in statuses)
