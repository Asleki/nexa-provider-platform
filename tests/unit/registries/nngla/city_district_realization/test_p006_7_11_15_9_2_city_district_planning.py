from registries.nngla.city_district_realization.planning import exact_partition_sql,require_complete_partition

def test_exact_predicate_is_st_equals(): assert exact_partition_sql().startswith("ST_Equals(")

def test_exact_complete_partition_passes():
    require_complete_partition({"all_valid":True,"all_non_empty":True,"all_polygonal":True,"all_covered_by_city":True,"union_equals_city":True,"sibling_positive_overlap_m2":0,"observed_count":8,"expected_count":8})

def test_inexact_partition_rejected():
    try: require_complete_partition({"all_valid":True,"all_non_empty":True,"all_polygonal":True,"all_covered_by_city":True,"union_equals_city":False,"sibling_positive_overlap_m2":0,"observed_count":8,"expected_count":8})
    except ValueError: return
    assert False
