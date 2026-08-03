from registries.name_authority.production_context import DeterministicDiverseSampler,get_plan

def test_sampling_is_reproducible_and_not_first_rows_only():
    rows=[{'id':str(i),'gender':'Male' if i%2 else 'Female','origin':f'O{i%3}','language':f'L{i%4}'} for i in range(20)]
    a=DeterministicDiverseSampler().sample(rows,10,42); b=DeterministicDiverseSampler().sample(rows,10,42)
    assert a.source_record_ids==b.source_record_ids and a.fingerprint==b.fingerprint
    assert a.source_record_ids!=tuple(str(i) for i in range(10))

def test_native_plan_has_three_sequential_types():
    p=get_plan('native-core'); assert [x.target_kind for x in p.steps]==['first_name','middle_name','surname']
