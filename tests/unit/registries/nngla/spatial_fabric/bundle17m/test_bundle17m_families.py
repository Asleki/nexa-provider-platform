
from registries.nngla.spatial_fabric.bundle17m import *

def test_19_data_driven_name_families_include_sea_route_and_6240_names():
    f=name_families(); assert len(f)==19 and governed_name_count()==6240 and 'SEA_ROUTE' in {x.name_family_code for x in f}; assert len(load_family_catalogue('SEA_ROUTE'))==180

def test_family_loader_uses_declared_id_field_and_prefix():
    f=family_map()['SETTLEMENT']; assert f.id_field=='settlement_name_record_id' and f.id_prefix=='NG-NAM-SET-'; assert load_family_catalogue('SETTLEMENT')[0][f.id_field].startswith(f.id_prefix)
