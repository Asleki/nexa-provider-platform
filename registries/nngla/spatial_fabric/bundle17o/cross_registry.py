"""Typed cross-registry NNGLA reference boundary."""
from ._shared import CROSS_REGISTRY_PATH,csv_rows
def reference_contracts(): return csv_rows(CROSS_REGISTRY_PATH)
def reference_allowed(consumer_registry: str, reference_family: str, purpose_code: str) -> bool:
    return any(
        r["consumer_registry"]==consumer_registry and r["reference_family"]==reference_family
        and r["purpose_code"]==purpose_code and r["status"]=="ACTIVE"
        for r in reference_contracts()
    )
__all__=["reference_contracts","reference_allowed"]
