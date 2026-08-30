from registries.nngla.city_containment_qualification.planning import execution_id, qualification_fingerprint, qualification_id


def test_qualification_identity_is_deterministic_and_policy_versioned():
    a = qualification_id(
        city_id="NG-ADM-000032",
        city_geometry_id="city-geometry:nngla:NG-ADM-000032:v1",
        parent_region_geometry_id="region-geometry:nngla:NG-ADM-000002:v1",
        qualification_policy_version=1,
    )
    b = qualification_id(
        city_id="NG-ADM-000032",
        city_geometry_id="city-geometry:nngla:NG-ADM-000032:v1",
        parent_region_geometry_id="region-geometry:nngla:NG-ADM-000002:v1",
        qualification_policy_version=1,
    )
    c = qualification_id(
        city_id="NG-ADM-000032",
        city_geometry_id="city-geometry:nngla:NG-ADM-000032:v1",
        parent_region_geometry_id="region-geometry:nngla:NG-ADM-000002:v1",
        qualification_policy_version=2,
    )
    assert a == b
    assert a != c
    assert a.startswith("city-containment:nngla:NG-ADM-000032:")


def test_plan_fingerprint_and_execution_identity_are_lowercase_sha256_governed():
    fingerprint = qualification_fingerprint({"cityId": "NG-ADM-000032", "value": 1})
    assert len(fingerprint) == 64
    assert execution_id(fingerprint) == f"nnglarun:city-containment-qualification:{fingerprint}"
