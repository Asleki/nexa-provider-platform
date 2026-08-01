from pathlib import Path
from registries.name_authority.models import SeedFileContract,SeedManifest,SeedRow
from registries.name_authority.adapters import ProductionSeedAdapter,load_tribe_ids
from registries.names.name_kind import NameKind

def manifest(file, family='test'):
    return SeedManifest(Path('/tmp/m.json'),'dataset.test',1,'Test','name_catalogue',family,'approved','utf-8',',',('simulation','production'),(file,),{})

def test_novegeo_mapping_and_tribe_reference():
    f=SeedFileContract('file.s','x','atomic_name',('id','name','tribe'),1,'0'*64,True,'surname',{'id':'external_record_id','name':'raw_name_value','tribe':'culture_refs[0]'})
    row=SeedRow(f,2,{'id':'sn_1','name':'Bregach','tribe':'trb_001'})
    c=ProductionSeedAdapter(manifest(f),'simulation',tribe_ids=frozenset({'trb_001'})).adapt(row,'batch:1')[0]
    assert c.name_kind is NameKind.SURNAME and c.culture_refs==('trb_001',) and c.external_record_id=='sn_1'

def test_multicultural_origin_is_preserved_as_unresolved_provenance():
    f=SeedFileContract('file.f','x','atomic_name',('ID','first_name','gender','origin','Language'),1,'0'*64,True,'first_name',{'ID':'external_record_id','first_name':'raw_name_value','gender':'sex_usage','origin':'attributes.source_origin','Language':'attributes.source_language'})
    row=SeedRow(f,2,{'ID':'1','first_name':'José','gender':'Male','origin':'Spain','Language':'Spanish'})
    c=ProductionSeedAdapter(manifest(f,'multicultural_atomic'),'production').adapt(row,'batch:1')[0]
    assert c.raw_name_value=='José' and c.attributes['seed']['origin_label']=='Spain' and c.language_refs==()

def test_immigration_row_yields_first_and_surname_candidates():
    f=SeedFileContract('file.p','x','paired_full_name_source',('id','first_name','second_name','origin','language'),1,'0'*64,True,None,{})
    row=SeedRow(f,2,{'id':'p1','first_name':'Daniel','second_name':'García Hernández','origin':'Spain','language':'Spanish'})
    values=ProductionSeedAdapter(manifest(f,'immigration_paired_names'),'simulation').adapt(row,'batch:1')
    assert [c.name_kind for c in values]==[NameKind.FIRST_NAME,NameKind.SURNAME]
    assert values[1].attributes['seed']['source_pair_id']=='p1'

def test_reference_loader_requires_unique_ids():
    f=SeedFileContract('file.t','x','supporting_reference',('id',),2,'0'*64,False,None,{})
    assert load_tribe_ids((SeedRow(f,2,{'id':'t1'}),SeedRow(f,3,{'id':'t2'})))==frozenset({'t1','t2'})
