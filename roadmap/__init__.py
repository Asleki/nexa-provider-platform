"""
Nexa Provider Platform (NPP) roadmap package.

This package contains the modular roadmap engine used by the top-level
``roadmap.py`` command-line interface.

The package initializer intentionally remains lightweight. It exposes stable
package metadata and compatibility information without importing unfinished
submodules or executing roadmap logic during import.

Planned package modules
-----------------------
- statuses.py
- models.py
- validation.py
- dependencies.py
- queries.py
- progress.py
- generator.py
- verification.py
- commands.py
- history.py

Public API policy
-----------------
Only names listed in ``__all__`` are considered part of the stable package
surface at this stage. Additional exports will be introduced deliberately as
the remaining modules are implemented and tested.
"""

from __future__ import annotations

from typing import Final

__title__: Final[str] = "Nexa Provider Platform Roadmap"
__package_name__: Final[str] = "roadmap"
__version__: Final[str] = "1.0.0"
__author__: Final[str] = "Nexa Provider Platform"
__license__: Final[str] = "Proprietary"
__description__: Final[str] = (
    "Modular roadmap engine for the Nexa Provider Platform."
)

PACKAGE_API_VERSION: Final[str] = "1"
ROADMAP_SCHEMA_VERSION: Final[str] = "1"

SUPPORTED_PYTHON: Final[tuple[int, int]] = (3, 10)

MODULES: Final[tuple[str, ...]] = (
    "statuses",
    "models",
    "validation",
    "dependencies",
    "queries",
    "progress",
    "generator",
    "verification",
    "commands",
    "history",
)


def get_version() -> str:
    """Return the roadmap package version."""

    return __version__


def get_package_info() -> dict[str, object]:
    """
    Return immutable-style package metadata as a new dictionary.

    A new dictionary is created for every call so callers cannot mutate module
    constants accidentally.
    """

    return {
        "title": __title__,
        "package_name": __package_name__,
        "version": __version__,
        "api_version": PACKAGE_API_VERSION,
        "roadmap_schema_version": ROADMAP_SCHEMA_VERSION,
        "author": __author__,
        "license": __license__,
        "description": __description__,
        "supported_python": SUPPORTED_PYTHON,
        "planned_modules": MODULES,
    }


def is_supported_python(
    version_info: tuple[int, int] | None = None,
) -> bool:
    """
    Return whether a Python major/minor version meets the package minimum.

    Parameters
    ----------
    version_info:
        Optional ``(major, minor)`` pair. When omitted, the running Python
        interpreter version is checked.
    """

    if version_info is None:
        import sys

        version_info = (sys.version_info.major, sys.version_info.minor)

    if (
        not isinstance(version_info, tuple)
        or len(version_info) != 2
        or not all(isinstance(value, int) for value in version_info)
    ):
        raise TypeError("version_info must be a (major, minor) integer tuple")

    return version_info >= SUPPORTED_PYTHON


__all__ = (
    "MODULES",
    "PACKAGE_API_VERSION",
    "ROADMAP_SCHEMA_VERSION",
    "SUPPORTED_PYTHON",
    "get_package_info",
    "get_version",
    "is_supported_python",
)
