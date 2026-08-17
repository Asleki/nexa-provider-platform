from datetime import date
from registries.nngla.spatial_fabric.bundle17k import form_subdivision,form_consolidation

def test_subdivision_creates_new_successor_parcel_identities_not_geometry_versions():
 r=form_subdivision('NV-01-001-0001',('NV-01-001-0002','NV-01-001-0003'),effective_on=date(2026,8,17),source_reference='test'); assert r.action.value=='SUBDIVISION' and len(r.successor_parcel_ids)==2
def test_consolidation_preserves_predecessor_lineage():
 r=form_consolidation(('NV-01-001-0002','NV-01-001-0003'),'NV-01-001-0004',effective_on=date(2026,8,18),source_reference='test'); assert r.action.value=='CONSOLIDATION' and len(r.predecessor_parcel_ids)==2
