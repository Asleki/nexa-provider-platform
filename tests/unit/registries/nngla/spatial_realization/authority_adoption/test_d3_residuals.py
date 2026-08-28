from registries.nngla.spatial_realization.authority_adoption.contracts import ResidualReviewStatus
from registries.nngla.spatial_realization.authority_adoption.residuals import build_residual


def test_unresolved_residual_is_internal_and_not_published():
    row = build_residual(parent_administrative_area_id="NG-ADM-000032", geometry_wkb_hex="010100000000000000000000000000000000000000",
        area_m2=0.0000001, adjacent_subject_ids=("NG-ADM-000036","NG-ADM-000037"),
        originating_target_ids=("fabric-face:nngla:x",), source_fingerprint="a"*64, runtime_fingerprint="b"*64,
        reason="ownership unresolved after exact qualification")
    assert row.review_status is ResidualReviewStatus.REVIEW_DEFERRED
    assert row.visibility == "INTERNAL"
    assert row.publication_status == "NOT_PUBLISHED"
