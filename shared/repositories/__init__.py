"""
============================================================
Nexa Provider Platform
Package: shared.repositories
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Public exports for the shared repository layer.
"""

from .base_repository import BaseRepository
from .local_repository import (
    DEFAULT_LOCAL_PROVIDER_ROOT,
    LocalRepository,
)
from .repository_errors import *
from .repository_factory import (
    RepositoryFactory,
    create_repository,
    get_default_repository_factory,
    get_default_repository_registry,
)
from .repository_interface import RepositoryInterface
from .repository_registry import (
    RepositoryClass,
    RepositoryRegistry,
    normalize_repository_type,
)
from .repository_result import RepositoryResult
from .repository_types import (
    RepositoryOperation,
    RepositoryType,
)

__all__ = [
    "BaseRepository",
    "DEFAULT_LOCAL_PROVIDER_ROOT",
    "LocalRepository",
    "RepositoryClass",
    "RepositoryFactory",
    "RepositoryInterface",
    "RepositoryOperation",
    "RepositoryRegistry",
    "RepositoryResult",
    "RepositoryType",
    "create_repository",
    "get_default_repository_factory",
    "get_default_repository_registry",
    "normalize_repository_type",
]
