from registries.nngla.spatial_fabric import source_inventory


def test_governed_identifier_validation_compiles_identifier_formats_once_per_process(monkeypatch):
    """Regression: Acode must not reread/recompile format CSVs for every identifier token."""
    source_inventory._compiled_formats.cache_clear()
    calls = 0
    original = source_inventory.load_identifier_formats

    def counted_load_identifier_formats():
        nonlocal calls
        calls += 1
        return original()

    monkeypatch.setattr(source_inventory, "load_identifier_formats", counted_load_identifier_formats)
    try:
        for _ in range(100):
            assert source_inventory.validate_governed_identifier("NG-SPT-000001")
            assert source_inventory.validate_governed_identifier("NG-SCELL-000001")
            assert not source_inventory.validate_governed_identifier("NG-MADE-UP-000001")
        assert calls == 1
        assert source_inventory._compiled_formats.cache_info().misses == 1
        assert source_inventory._compiled_formats.cache_info().hits >= 299
    finally:
        source_inventory._compiled_formats.cache_clear()
