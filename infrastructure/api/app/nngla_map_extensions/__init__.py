"""Generic additive NNGLA national-map extension seam."""
from .contracts import NNGLAMapExtensionContext
from .loader import (
    EXTENSION_MANIFEST_VERSION,
    EXTENSION_MODULE_PREFIX,
    NNGLAMapExtensionManifestError,
    compose_nngla_map_extensions,
)

__all__ = [
    "EXTENSION_MANIFEST_VERSION",
    "EXTENSION_MODULE_PREFIX",
    "NNGLAMapExtensionContext",
    "NNGLAMapExtensionManifestError",
    "compose_nngla_map_extensions",
]
