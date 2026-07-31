import pytest
from registries.adapters.postgresql import PostgreSQLConnectionProvider
def test_provider_is_lazy():
    calls=[]; provider=PostgreSQLConnectionProvider(lambda:calls.append(1) or object())
    assert calls==[]; assert provider.connect() is not None; assert calls==[1]
def test_none_rejected():
    with pytest.raises(RuntimeError): PostgreSQLConnectionProvider(lambda:None).connect()
