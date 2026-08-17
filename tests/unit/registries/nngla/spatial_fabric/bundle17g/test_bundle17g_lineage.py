from registries.nngla.spatial_fabric.bundle17g import ParcelLineageCandidate, promote_lineage_candidate


def test_subdivision_candidate_promotes_into_locked_lineage_contract_without_rewriting_predecessor():
    candidate = ParcelLineageCandidate(
        "parcel-lineage-candidate:000001", "SUBDIVISION", ("NV-12-004-8890",),
        ("NV-12-004-8891", "NV-12-004-8892"), "2026-08-17", "test:subdivision"
    )
    record = promote_lineage_candidate(candidate)
    assert record.lineage_id == "parcel-lineage:000001"
    assert record.predecessor_parcel_ids == ("NV-12-004-8890",)
    assert record.successor_parcel_ids == ("NV-12-004-8891", "NV-12-004-8892")
