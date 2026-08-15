from dataclasses import replace
import pytest

from registries.nngla.migration_architecture.execution import ExecutionError, ExecutionRequest, ExecutionService, confirmation_token
from registries.nngla.migration_architecture.persistence import MemoryExecutionRepository, canonical_payload_sha256
from registries.nngla.migration_architecture.selectors import Selector
from registries.nngla.migration_architecture.source_catalogue import load_source
from registries.nngla.migration_architecture.verification import qualify_rerun, verify_receipt

CAPS={"nngla_execution_foundation","nngla_geographic_identity_places","nngla_geometry_roads_addresses","nngla_cadastre_titles_state_land","world_geometry_authority"}

def request(service, plan="roads", selector=None, fingerprint=None, confirmation=None):
    preview=service.preview_for_execution(plan,selector_override=selector,repository_revision="e0fcc99")
    return ExecutionRequest(plan,"e0fcc99","actor:submitter","actor:approver",fingerprint or preview.fingerprint,
        confirmation or confirmation_token(plan,"npp_dev",preview.fingerprint),selector),preview

def test_bundle16c_exact_road_batch_executes_and_reruns_without_duplicates():
    repo=MemoryExecutionRepository(capabilities=CAPS); service=ExecutionService(repo); selector=Selector(limit=5)
    req,preview=request(service,selector=selector); first=service.run(req)
    assert first.inserted_count==5 and first.reused_count==0 and first.failed_count==0
    assert set(repo.canonical)=={f"NG-RD-{i:06d}" for i in range(1,6)}
    req2,preview2=request(service,selector=selector); second=service.run(req2)
    assert preview.fingerprint==preview2.fingerprint
    assert second.inserted_count==0 and second.reused_count==5
    assert qualify_rerun(first,second).passed is True
    assert verify_receipt(second).passed is True

def test_bundle16c_confirmation_and_fingerprint_fail_closed():
    repo=MemoryExecutionRepository(capabilities=CAPS); service=ExecutionService(repo); selector=Selector(limit=1)
    req,preview=request(service,selector=selector)
    with pytest.raises(ExecutionError,match="confirmation"):
        service.run(replace(req,confirmation="yes"))
    with pytest.raises(ExecutionError,match="fingerprint"):
        service.run(replace(req,approved_fingerprint="0"*64,confirmation=confirmation_token("roads","npp_dev","0"*64)))

def test_bundle16c_same_source_id_with_changed_payload_is_conflict():
    repo=MemoryExecutionRepository(capabilities=CAPS); service=ExecutionService(repo); selector=Selector(limit=1)
    req,_=request(service,selector=selector); service.run(req)
    mapping=repo.crosswalks["NG-RD-CAND-000001"]
    repo.crosswalks["NG-RD-CAND-000001"]=replace(mapping,source_payload_sha256="f"*64)
    req2,_=request(service,selector=selector)
    with pytest.raises(ExecutionError,match="SOURCE_ID_CONFLICT"):
        service.run(req2)

def test_bundle16c_execution_requires_foundation_capability_even_if_domain_schema_exists():
    repo=MemoryExecutionRepository(capabilities={"nngla_geometry_roads_addresses"}); service=ExecutionService(repo)
    preview=service.preview_for_execution("roads",selector_override=Selector(limit=1),repository_revision="x")
    assert preview.schema_ready is False and preview.execution_ready is False

def test_bundle16c_empty_governed_register_executes_as_empty_receipt():
    repo=MemoryExecutionRepository(capabilities=CAPS); service=ExecutionService(repo)
    req,preview=request(service,plan="addresses"); receipt=service.run(req)
    assert preview.selected_count==0
    assert receipt.status=="EMPTY" and receipt.selected_count==0 and receipt.inserted_count==0
