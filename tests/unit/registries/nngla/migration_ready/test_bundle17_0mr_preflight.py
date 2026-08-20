from registries.nngla.migration_ready import preflight as module
from registries.nngla.migration_ready.contracts import BaselineVerificationReport, CandidateStateReport


def _candidate():
    return CandidateStateReport(900, 350, 550, 37, 21, 5, 11, ())


def _baseline():
    return BaselineVerificationReport(1284, 1284, (), (), True, ())


def test_preflight_requires_18_migrations_tls_schema_baseline_and_source_guards(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "_target_metadata", lambda connection: ("npp_dev", "npp_admin", True))
    monkeypatch.setattr(module, "_relation_status", lambda connection: {x: True for x in module.REQUIRED_RELATIONS})
    monkeypatch.setattr(module, "_function_status", lambda connection: {f"geography.{x}": True for x in module.REQUIRED_FUNCTIONS})
    monkeypatch.setattr(module, "_migration_ledger_state", lambda connection: (18, 0, (), ()))
    monkeypatch.setattr(module, "assess_empty_registers", lambda root, connection: (object(),))
    monkeypatch.setattr(module, "empty_registers_ready", lambda statuses: True)
    monkeypatch.setattr(module, "assess_candidate_state", lambda root: _candidate())
    monkeypatch.setattr(module, "verify_immutable_baseline", lambda root, connection: _baseline())
    monkeypatch.setattr(module, "bundle17e_is_qualified", lambda: True)
    report = module.inspect_preflight(tmp_path, object(), "development")
    assert report.ready
    assert report.migration_ledger_applied == 18


def test_preflight_fails_when_governed_schema_catalogue_is_incomplete(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "_target_metadata", lambda connection: ("npp_dev", "npp_admin", True))
    monkeypatch.setattr(module, "_relation_status", lambda connection: {x: True for x in module.REQUIRED_RELATIONS})
    monkeypatch.setattr(module, "_function_status", lambda connection: {f"geography.{x}": True for x in module.REQUIRED_FUNCTIONS})
    monkeypatch.setattr(module, "_migration_ledger_state", lambda connection: (17, 0, ("m006_07_11_nngla_spatial_query_read_models",), ()))
    monkeypatch.setattr(module, "assess_empty_registers", lambda root, connection: (object(),))
    monkeypatch.setattr(module, "empty_registers_ready", lambda statuses: True)
    monkeypatch.setattr(module, "assess_candidate_state", lambda root: _candidate())
    monkeypatch.setattr(module, "verify_immutable_baseline", lambda root, connection: _baseline())
    monkeypatch.setattr(module, "bundle17e_is_qualified", lambda: True)
    report = module.inspect_preflight(tmp_path, object(), "development")
    assert not report.ready
    assert any(x.startswith("MIGRATION_LEDGER_REQUIRED_BASELINE_NOT_APPLIED") for x in report.findings)
