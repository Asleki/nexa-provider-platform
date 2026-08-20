import json

from registries.nngla.migration_ready.cli import main


def test_inventory_is_offline_and_zero_write(capsys):
    assert main(["inventory"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["database_writes"] == 0
    assert payload["batch_profiles"]["initial-spatial-2411"]["batch_sizes"] == [11, 800, 800, 800]
