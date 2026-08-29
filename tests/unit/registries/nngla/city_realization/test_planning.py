from registries.nngla.city_realization.planning import (
    city_geometry_id,
    city_publication_id,
    execution_id,
    fingerprint_payload,
)


def test_deterministic_identifiers_are_separate_and_versioned():
    city = "NG-ADM-000170"
    assert city_geometry_id(city) == "city-geometry:nngla:NG-ADM-000170:v1"
    assert city_publication_id(city) == "city-publication:nngla:NG-ADM-000170:v1"
    assert city_geometry_id(city, 2).endswith(":v2")


def test_plan_fingerprint_is_order_independent_and_execution_id_is_derived():
    left = fingerprint_payload({"cityId": "NG-ADM-000170", "areaM2": 2.0})
    right = fingerprint_payload({"areaM2": 2.0, "cityId": "NG-ADM-000170"})
    assert left == right
    assert len(left) == 64
    assert execution_id(left) == f"nnglarun:city-realization:{left}"
