from .query_catalogue import query_definitions,result_contract_rows
from .geocoding import geocoding_rules
from .cross_registry import reference_contracts
from ._shared import READ_MODEL_CATALOGUE_PATH,csv_rows
from .postgresql_contract import load_schema17o_sql,qualify_schema17o_sql
REQUIRED_OPERATORS=frozenset({"CONTAINS","WITHIN","INTERSECTS","CROSSES","TOUCHES","ADJACENT","NEAREST","DISTANCE","FRONTS","CONNECTED_TO"})
def bundle17o_is_qualified():
    defs=query_definitions(); ops={d.operator_code for d in defs if d.operator_code}
    return (
        REQUIRED_OPERATORS<=ops
        and {"GEOCODE","REVERSE_GEOCODE","FIND_BY_CANONICAL_ID"}<={d.query_code for d in defs}
        and len(result_contract_rows())==len(defs)
        and len(csv_rows(READ_MODEL_CATALOGUE_PATH))>=4
        and {"NFKC","CASEFOLD","COLLAPSE_WHITESPACE"}<={r["normalization_step"] for r in geocoding_rules()}
        and len(reference_contracts())>=10
        and qualify_schema17o_sql(load_schema17o_sql())==()
    )
__all__=["REQUIRED_OPERATORS","bundle17o_is_qualified"]
