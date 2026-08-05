import pytest
from infrastructure.governance.qualification import *
from infrastructure.governance.validation import ValidationContext,ValidationOutcome,ValidationReceipt
from infrastructure.governance.publication import *
def test_qualification_requires_independent_actors():
    with pytest.raises(ValueError): QualificationRequest("qualification:1","validation:1","actor:x","actor:x")
def test_publication_rejects_internal_visibility():
    with pytest.raises(ValueError): PublicationRecord("publication:1","dataset:1",1,"T","production","internal","active",{})
def test_publication_service_returns_only_eligible_records():
    service=PublicationService(InMemoryPublicationRepository())
    rec=PublicationRecord("publication:1","dataset:1",1,"T","production","public","active",{"x":1})
    service.publish(rec)
    assert service.get_public("publication:1").etag.startswith('"sha256:')
