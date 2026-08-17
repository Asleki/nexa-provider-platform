"""Data-driven spatial query catalogue/result-contract registry."""
from ._shared import QUERY_CATALOGUE_PATH, QUERY_RESULT_CONTRACTS_PATH, csv_rows
from .contracts import QueryDefinition

def query_definitions() -> tuple[QueryDefinition,...]:
    return tuple(QueryDefinition(
        row["query_code"],int(row["query_version"]),row["operator_code"],row["input_contract"],
        row["result_contract"],row["visibility_policy"],row["backend_capability"],row["status"]
    ) for row in csv_rows(QUERY_CATALOGUE_PATH))
def query_map():
    rows=query_definitions(); out={r.query_code:r for r in rows}
    if len(out)!=len(rows): raise ValueError("duplicate query_code")
    return out
def get_query_definition(code: str, version: int=1):
    item=query_map().get(str(code).strip().upper())
    if item is None or item.query_version!=version or item.status!="ACTIVE": raise KeyError(f"unsupported spatial query: {code} v{version}")
    return item
def result_contract_rows(): return csv_rows(QUERY_RESULT_CONTRACTS_PATH)
__all__=["query_definitions","query_map","get_query_definition","result_contract_rows"]
