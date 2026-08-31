from registries.nngla.municipality_realization.planning import (
    municipality_geometry_id, municipality_publication_id,
    partition_qualification_id, member_set_payload, canonical_sha256,
)

def test_ids_are_stable_and_versioned():
    assert municipality_geometry_id("NG-ADM-000010") == "municipality-geometry:nngla:NG-ADM-000010:v1"
    assert municipality_publication_id("NG-ADM-000010") == "municipality-publication:nngla:NG-ADM-000010:v1"
    assert partition_qualification_id("NG-ADM-000001") == "municipality-partition:nngla:NG-ADM-000001:v1"

def test_member_set_is_canonical_sorted_and_hashable():
    rows = member_set_payload([
        {"municipalityId":"NG-ADM-000012","geometryId":"g2","geometrySha256":"b"*64},
        {"municipalityId":"NG-ADM-000010","geometryId":"g1","geometrySha256":"a"*64},
    ])
    assert [row["municipalityId"] for row in rows] == ["NG-ADM-000010","NG-ADM-000012"]
    assert len(canonical_sha256(rows)) == 64
