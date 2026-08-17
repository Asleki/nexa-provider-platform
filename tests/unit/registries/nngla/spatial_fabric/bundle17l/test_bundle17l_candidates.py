
from registries.nngla.spatial_fabric.bundle17l import recognition_candidates,observation_links,form_candidate

def test_source_reconciliation_separates_candidates_from_canonical_identity():
    c=recognition_candidates(); assert len(c)==37; existing=[x for x in c if x.existing_canonical_feature_id]; assert len(existing)==21 and {x.existing_canonical_feature_id for x in existing}=={f'NG-FEAT-{i:06d}' for i in range(1,22)}; assert all(x.candidate_id.startswith('featcand:nngla:') for x in c)
def test_observation_links_preserve_multi_source_evidence_without_duplicate_features():
    links=observation_links(); assert len(links)==49 and len({x.link_id for x in links})==49; assert sum(x.observation_type=='QUALIFIED_LANDFORM_CANDIDATE' for x in links)==12
def test_simulation_candidate_formation_does_not_mint_ng_feat():
    c=form_candidate(source_feature_id='simulation:hill:1',feature_type_code='HILL',source_dataset_id='sim:test',source_record_reference='event:1'); assert c.runtime_mode=='simulation' and c.existing_canonical_feature_id=='' and c.candidate_id.startswith('featcand:nngla:')
