import pytest
from database.reference_qualification.development_reset import DevelopmentCatalogueReset

def test_reset_restricted_to_dev_target():
    with pytest.raises(ValueError): DevelopmentCatalogueReset(lambda:None).preview('prod','production')
