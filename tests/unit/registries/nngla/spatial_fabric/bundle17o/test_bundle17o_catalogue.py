from registries.nngla.spatial_fabric.bundle17o.query_catalogue import query_definitions,get_query_definition,result_contract_rows
def test_query_catalogue_covers_locked_vocabulary_and_special_queries():
    ops={q.operator_code for q in query_definitions() if q.operator_code}
    assert {"CONTAINS","WITHIN","INTERSECTS","CROSSES","TOUCHES","ADJACENT","NEAREST","DISTANCE","FRONTS","CONNECTED_TO"}<=ops
    assert get_query_definition("GEOCODE").result_contract=="GEOCODE_RESULT"
    assert len(result_contract_rows())==len(query_definitions())
