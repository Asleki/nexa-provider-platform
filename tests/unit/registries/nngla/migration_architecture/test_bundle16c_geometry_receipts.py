from registries.nngla.migration_architecture.geometry_payloads import load_geometry
from registries.nngla.migration_architecture.source_catalogue import load_source
from registries.nngla.migration_architecture.receipts import ExecutionReceipt, ExecutionItemReceipt, utc_now
from registries.nngla.migration_architecture.verification import verify_receipt

def test_bundle16c_all_current_geometry_candidates_resolve_real_governed_geometry():
    snapshot=load_source("geometry")
    assert len(snapshot.records)==21
    for record in snapshot.records:
        geometry=load_geometry(record)
        assert geometry["type"].upper()==record.payload["geometry_type_code"]
        assert geometry["coordinates"]

def test_bundle16c_execution_receipt_is_machine_verifiable_and_content_hashed():
    now=utc_now(); item=ExecutionItemReceipt("source:1","INSERTED","NG-RD-000001",publication_ready=True)
    receipt=ExecutionReceipt("nnglarun:test","roads",1,"a"*64,"npp_dev","development","production","rev","b"*64,
        "actor:a","actor:b",1,1,0,0,0,"APPLIED",now,now,(item,))
    assert verify_receipt(receipt).passed is True
    assert len(receipt.content_sha256)==64
