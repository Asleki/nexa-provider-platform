from registries.nngla.spatial_fabric.bundle21a.source import current_candidates
from registries.nngla.spatial_fabric.bundle21a.eligibility import decide

def test_current_state_fails_closed_without_publication_gate():
    d=[decide(c) for c in current_candidates()]
    assert all(x.decision=='BLOCKED' and not x.map_renderable and not x.publication_id for x in d)
    assert all('NO_NNGLA_PUBLICATION_RECORD' in x.reasons for x in d)
