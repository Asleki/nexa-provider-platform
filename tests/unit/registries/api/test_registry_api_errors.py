from registries.api import RegistryApiError, RegistryApiExecutionError

def test_execution_error_belongs_to_registry_api_hierarchy():
    assert issubclass(RegistryApiExecutionError, RegistryApiError)
