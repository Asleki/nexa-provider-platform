import inspect
from registries.api import RegistryApiRequest, RegistryApiResponse
from registries.audit import RegistryAuditResult
from registries.ports import RegistryAuditPort


def test_registry_audit_port_declares_complete_record_contract() -> None:
    signature = inspect.signature(RegistryAuditPort.record)

    assert tuple(signature.parameters) == ("self", "request", "response")
    assert signature.parameters["request"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["response"].kind is inspect.Parameter.KEYWORD_ONLY

    annotations = RegistryAuditPort.record.__annotations__
    assert "RegistryApiRequest" in str(annotations["request"])
    assert "RegistryApiResponse" in str(annotations["response"])
    assert "RegistryAuditResult" in str(annotations["return"])


def test_concrete_port_implementation_must_override_record() -> None:
    class MissingRecord(RegistryAuditPort):
        pass

    try:
        MissingRecord()
    except TypeError:
        pass
    else:
        raise AssertionError("RegistryAuditPort must remain abstract")
