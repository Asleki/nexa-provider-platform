import registries.audit as registry_audit


EXPECTED_EXPORTS = {
    "REGISTRY_AUDIT_ERROR_PREFIX",
    "RegistryAuditConfigurationError",
    "RegistryAuditContext",
    "RegistryAuditError",
    "RegistryAuditExecutionError",
    "RegistryAuditIntegration",
    "RegistryAuditPolicy",
    "RegistryAuditRecordFactory",
    "RegistryAuditResult",
    "RegistryAuditResultError",
    "RegistryAuditValidationError",
}


def test_registry_audit_exports_are_explicit_and_deterministic() -> None:
    assert set(registry_audit.__all__) == EXPECTED_EXPORTS
    assert len(registry_audit.__all__) == len(set(registry_audit.__all__))
    assert all(hasattr(registry_audit, name) for name in registry_audit.__all__)


def test_registry_audit_does_not_export_internal_module_symbols() -> None:
    assert "MappingProxyType" not in registry_audit.__all__
    assert "Any" not in registry_audit.__all__
    assert "Mapping" not in registry_audit.__all__
