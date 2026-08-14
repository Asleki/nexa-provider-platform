from collections import Counter
from registries.nngla.bundle15a_source import load_places, load_administrative_areas
from registries.nngla.places import MemoryPlaceRepository
from registries.nngla.administrative_areas import MemoryAdministrativeAreaRepository
from registries.nngla.place_hierarchy import qualify_place_hierarchy

def test_700_place_source_corpus_is_preserved_without_inventing_geometry():
    places=load_places()
    assert len(places)==700
    assert all(not p.has_authoritative_geometry for p in places)
    assert all(p.spatial_assignment_status=='UNMAPPED_PENDING_ASSOCIATION' for p in places)
    assert sum(1 for p in places if p.is_national_capital)==1
    capital=next(p for p in places if p.is_national_capital)
    assert capital.canonical_name=='Orivane'

def test_place_type_population_matches_governed_source():
    counts=Counter(p.place_type_code for p in load_places())
    assert counts == {'VILLAGE':240,'TOWN':120,'SUBURB':96,'TOWNSHIP':72,'CITY_DISTRICT':64,'MARKET_CENTRE':40,'MUNICIPALITY':24,'INDUSTRIAL_ZONE':16,'RESORT_SETTLEMENT':12,'CITY':8,'ISLAND_SETTLEMENT':8}

def test_192_admin_candidates_are_ready_nonspatial_and_boundary_deferred():
    areas=load_administrative_areas(); repo=MemoryAdministrativeAreaRepository()
    assert len(areas)==192
    for a in areas: repo.add(a)
    assert all(a.is_nonspatial_ready for a in areas)
    assert all(a.boundary_status=='BOUNDARY_PENDING_LEGALIZATION' for a in areas)
    assert all(a.geometry_reference is None for a in areas)
    assert repo.by_source('NGR-01').canonical_name=='Orivane Capital Territory'

def test_nonspatial_hierarchy_qualifies_without_authoritative_geometry():
    assert qualify_place_hierarchy(load_places(), load_administrative_areas()) == ()
