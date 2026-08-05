import pytest
from infrastructure.api.config import InfrastructureSettings
from infrastructure.database.runtime import DatabaseRuntimeSettings
def test_api_settings_are_safe_and_immutable():
    value=InfrastructureSettings.from_mapping({"INFRA_ENVIRONMENT":"testing","INFRA_ALLOWED_ORIGINS":"https://example.test"})
    assert value.allowed_origins==("https://example.test",)
    with pytest.raises(Exception): value.environment_name="production"
def test_production_rejects_wildcard_cors():
    with pytest.raises(ValueError): InfrastructureSettings(environment_name="production",allowed_origins=("*",))
def test_database_safe_summary_omits_password():
    s=DatabaseRuntimeSettings("db",5432,"npp_dev","user","secret")
    assert "password" not in str(s.safe_summary()).lower()
