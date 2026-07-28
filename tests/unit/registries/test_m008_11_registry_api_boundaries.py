import ast
from pathlib import Path
from registries.api import RegistryApi, RegistryApiOperation

ROOT=Path(__file__).resolve().parents[3]
API=ROOT/"registries"/"api"

def _imports(path):
    tree=ast.parse(path.read_text(),filename=str(path)); found=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): found.extend(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module: found.append(node.module)
    return found

def test_m008_11_appends_without_removing_previous_boundaries():
    root=ROOT/"tests"/"unit"/"registries"
    for milestone in range(1,11): assert list(root.glob(f"test_m008_{milestone}_*boundaries.py"))

def test_registry_api_is_internal_and_clear_is_not_exposed():
    assert RegistryApi is not None
    assert "clear" not in {item.value for item in RegistryApiOperation}

def test_registry_api_has_no_transport_shared_audit_or_adapter_coupling():
    forbidden=("fastapi","flask","django","requests","httpx","shared.audit","registries.adapters","supabase","database","backend","services")
    violations=[]
    for path in API.glob("*.py"):
        for item in _imports(path):
            if item.startswith(forbidden): violations.append(f"{path.name}: {item}")
    assert violations==[]

def test_registry_api_does_not_publish_persist_events_or_clear_repository():
    source="\n".join(path.read_text() for path in API.glob("*.py")).lower()
    for token in (".publish(","eventrepository","auditrepository","repository.clear(","apirouter","fastapi"):
        assert token not in source

def test_later_audit_metadata_relationship_layers_remain_absent():
    path=ROOT/"registries"/"metadata"
    assert not path.exists() or not any(path.glob("*.py"))
    api_source="\n".join(path.read_text() for path in API.glob("*.py"))
    for token in ("training_eligibility","retention_policy","relationship_provenance"):
        assert token not in api_source
