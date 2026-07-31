from datetime import datetime,timezone
import pytest
from registries.name_imports.name_candidate import NameCandidate
from registries.name_imports.name_candidate_status import NameCandidateStatus

def candidate(**changes):
    data=dict(candidate_id="candidate:1",batch_id="batch:1",source_id="source:1",source_row_number=2,raw_name_value=" Alex ",name_kind="first_name",runtime_mode="simulation",created_at=datetime(2026,1,1,tzinfo=timezone.utc))
    data.update(changes); return NameCandidate(**data)

def test_candidate_is_normalized_immutable_and_uses_separate_identity():
    c=candidate(language_refs="lang:en|lang:sn")
    assert c.raw_name_value=="Alex" and c.candidate_id!="name:1"
    assert c.language_refs==("lang:en","lang:sn") and c.status is NameCandidateStatus.STAGED
    with pytest.raises(TypeError): c.attributes["x"]=1

def test_candidate_requires_safe_ids_row_runtime_and_aware_time():
    for changes in ({"candidate_id":"bad id"},{"source_row_number":1},{"runtime_mode":"Production Mode"},{"created_at":datetime(2026,1,1)}):
        with pytest.raises((TypeError,ValueError)): candidate(**changes)

def test_with_status_returns_new_candidate():
    original=candidate(); updated=original.with_status("validated")
    assert original.status is NameCandidateStatus.STAGED
    assert updated.status is NameCandidateStatus.VALIDATED
