from registries.nngla.bundle15c_qualification import qualify_bundle15c

def test_bundle15c_qualification_is_green_without_fabricating_parcels_titles_or_state_land():
    q=qualify_bundle15c()
    assert q.status=='QUALIFIED' and q.findings==()
    assert (q.land_use_count,q.tenure_type_count,q.title_type_count,q.state_land_category_count)==(13,7,6,6)
    assert (q.parcel_bootstrap_count,q.title_bootstrap_count,q.state_land_bootstrap_count)==(0,0,0)

def test_bundle15c_qualification_preserves_joint_ownership_extension_and_nnlgla_master_boundary():
    q=qualify_bundle15c(); assert q.status=='QUALIFIED'
    # Consumer real-estate systems are not an NNGLA authority source or schema dependency.
    assert all('consumer-domain-leak' not in x for x in q.findings)
