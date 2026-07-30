"""Errors raised by name catalogue repositories."""
class NameRepositoryError(RuntimeError): pass
class NameNotFoundError(NameRepositoryError): pass
class NameAlreadyExistsError(NameRepositoryError): pass
class NameIdentityConflictError(NameRepositoryError): pass
class NameRepositoryOperationError(NameRepositoryError): pass
__all__=["NameRepositoryError","NameNotFoundError","NameAlreadyExistsError","NameIdentityConflictError","NameRepositoryOperationError"]
