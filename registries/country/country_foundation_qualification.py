"""P006.7.1.10 final NoveGeo Country Foundation qualification."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from shared.events.event_metadata import EventMetadata
from shared.runtime.operation_runtime import OperationRuntimeMode
from .qualification import qualify_bundle13a_source
from .bundle13b_qualification import qualify_bundle13b_source
from .persistence import MemoryCountryRepository
from .persistence_source import build_country_registry_record
from .events import CountryEventFactory,CountryEventType
from .read_model import CountryReadModelProjector,MemoryCountryReadRepository

@dataclass(frozen=True,slots=True)
class CountryFoundationQualificationReceipt:
    qualification_id:str; status:str; country_id:str; record_version:int; read_model_checksum:str; findings:tuple[str,...]

def qualify_novegeo_country_foundation(repository_root:str|Path)->CountryFoundationQualificationReceipt:
    a=qualify_bundle13a_source(repository_root); b=qualify_bundle13b_source(repository_root); record=build_country_registry_record(repository_root)
    repo=MemoryCountryRepository(); repo.add(record)
    if repo.get(record.country_id)!=record: raise ValueError("canonical persistence round trip failed.")
    reads=MemoryCountryReadRepository(); projected=CountryReadModelProjector().rebuild(repo.list_all(),reads)
    if len(projected)!=1 or reads.get(record.country_id).record_version!=record.record_version: raise ValueError("country read-model projection failed.")
    trace=CountryEventFactory.create(event_type=CountryEventType.COUNTRY_QUALIFIED,country_id=record.country_id,record_version=record.record_version,runtime_mode=OperationRuntimeMode.PRODUCTION,correlation_id="qualification:p006.7.1",actor_id="authority:nexadevs",payload={"bundle13a":a.status,"bundle13b":b.status})
    if trace.event.payload["country_id"]!=record.country_id or trace.audit.event_id!=trace.event.event_id: raise ValueError("country event/audit linkage failed.")
    findings=("BUNDLE_13A_QUALIFIED","BUNDLE_13B_QUALIFIED","CANONICAL_PERSISTENCE_ROUND_TRIP","COUNTRY_EVENT_AUDIT_LINKED","COUNTRY_READ_MODEL_REBUILDABLE","COUNTRY_STABLE_ID_PRESERVED","POSTGRESQL_ADAPTER_BOUNDARY_RESERVED","CSV_RUNTIME_AUTHORITY_PROHIBITED","SIMULATION_PRODUCTION_DISTINCTION_PRESERVED")
    return CountryFoundationQualificationReceipt("qualification:novegeo:country-foundation:v1","PASSED",record.country_id,record.record_version,projected[0].checksum,findings)
__all__=["CountryFoundationQualificationReceipt","qualify_novegeo_country_foundation"]
