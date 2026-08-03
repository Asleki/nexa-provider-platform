from registries.reference_authority import *

def test_reference_authoring_allocates_and_reuses():
    repo=MemoryReferenceRepository(); n=iter([1,2]); svc=ReferenceAuthoringService(repo,AtomicReferenceCodeAllocator(lambda _:next(n)))
    req=ReferenceAuthoringRequest('language',' Spanish ','author','approver','fixture')
    first,created=svc.author(req); second,created2=svc.author(req)
    assert created is True and created2 is False
    assert first.reference_code=='lng_001' and second.reference_id==first.reference_id

def test_origin_requires_distinct_actors():
    import pytest
    with pytest.raises(ValueError): ReferenceAuthoringRequest('origin','Spain','same','same','fixture')

def test_reference_code_contract():
    import pytest
    with pytest.raises(ValueError): ReferenceRecord('x','trb_1','tribe','X',created_by_actor_id='a',approved_by_actor_id='b')
