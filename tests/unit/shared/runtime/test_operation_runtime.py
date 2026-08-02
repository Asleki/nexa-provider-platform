import pytest

from shared.runtime.operation_runtime import (
    ENV_OPERATION_RUNTIME_MODE,
    OperationRuntimeMode,
    SUPPORTED_OPERATION_RUNTIME_MODES,
)


def test_operation_runtime_contract_keeps_simulation_and_production_distinct():
    assert OperationRuntimeMode.SIMULATION.value == "simulation"
    assert OperationRuntimeMode.PRODUCTION.value == "production"
    assert SUPPORTED_OPERATION_RUNTIME_MODES == ("simulation", "production")
    assert ENV_OPERATION_RUNTIME_MODE == "NPP_RUNTIME_MODE"


def test_operation_runtime_parser_normalizes_approved_values():
    assert OperationRuntimeMode.parse(" SIMULATION ") is OperationRuntimeMode.SIMULATION
    assert OperationRuntimeMode.parse("Production") is OperationRuntimeMode.PRODUCTION


def test_operation_runtime_parser_rejects_unknown_value():
    with pytest.raises(ValueError, match="valid modes: simulation, production"):
        OperationRuntimeMode.parse("demo")
