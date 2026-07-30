from registries.names import NameAlreadyExistsError,NameIdentityConflictError,NameNotFoundError,NameRepositoryError

def test_repository_errors_share_domain_base():
    assert issubclass(NameAlreadyExistsError,NameRepositoryError)
    assert issubclass(NameIdentityConflictError,NameRepositoryError)
    assert issubclass(NameNotFoundError,NameRepositoryError)
