"""Fail-closed loader for additive NNGLA map extension composition."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import re
from typing import Callable

from .contracts import NNGLAMapExtensionContext


EXTENSION_MANIFEST_VERSION = 1
EXTENSION_MODULE_PREFIX = "infrastructure.api.app.nngla_map_extensions.layers."
_EXTENSION_ID_PATTERN = re.compile(r"^nngla-map-extension:[a-z0-9][a-z0-9-]*:v[1-9][0-9]*$")
_DEFAULT_MANIFEST_PATH = Path(__file__).with_name("extension_manifest.json")


class NNGLAMapExtensionManifestError(RuntimeError):
    """Raised when an extension manifest or extension module is not trustworthy."""


def _load_manifest(path: Path) -> tuple[dict[str, object], ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NNGLAMapExtensionManifestError("NNGLA map extension manifest is unreadable") from exc
    if not isinstance(payload, dict):
        raise NNGLAMapExtensionManifestError("NNGLA map extension manifest must be an object")
    if payload.get("manifestVersion") != EXTENSION_MANIFEST_VERSION:
        raise NNGLAMapExtensionManifestError("unsupported NNGLA map extension manifest version")
    extensions = payload.get("extensions")
    if not isinstance(extensions, list):
        raise NNGLAMapExtensionManifestError("NNGLA map extension manifest extensions must be a list")

    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    seen_modules: set[str] = set()
    previous_order = -1
    for raw in extensions:
        if not isinstance(raw, dict) or set(raw) != {"extensionId", "order", "module"}:
            raise NNGLAMapExtensionManifestError("each map extension requires extensionId, order and module")
        extension_id = str(raw["extensionId"])
        module = str(raw["module"])
        order = raw["order"]
        if not _EXTENSION_ID_PATTERN.fullmatch(extension_id):
            raise NNGLAMapExtensionManifestError(f"invalid map extension id: {extension_id}")
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise NNGLAMapExtensionManifestError(f"invalid map extension order for {extension_id}")
        if order <= previous_order:
            raise NNGLAMapExtensionManifestError("map extension order must be strictly increasing")
        if not module.startswith(EXTENSION_MODULE_PREFIX):
            raise NNGLAMapExtensionManifestError(f"map extension module outside constrained namespace: {module}")
        if module.endswith(".__init__") or ".contracts" in module or ".loader" in module:
            raise NNGLAMapExtensionManifestError(f"reserved map extension module: {module}")
        if extension_id in seen_ids or module in seen_modules:
            raise NNGLAMapExtensionManifestError("duplicate map extension id or module")
        seen_ids.add(extension_id)
        seen_modules.add(module)
        previous_order = order
        normalized.append({"extensionId": extension_id, "order": order, "module": module})
    return tuple(normalized)


def compose_nngla_map_extensions(
    context: NNGLAMapExtensionContext,
    *,
    manifest_path: str | Path | None = None,
    import_module: Callable[[str], object] = importlib.import_module,
) -> NNGLAMapExtensionContext:
    """Apply every registered extension in deterministic manifest order.

    The manifest is intentionally append-only.  An empty manifest is identity
    composition and therefore preserves the locked REGION→CITY runtime exactly.
    """

    if not isinstance(context, NNGLAMapExtensionContext):
        raise TypeError("context must be NNGLAMapExtensionContext")
    path = Path(manifest_path) if manifest_path is not None else _DEFAULT_MANIFEST_PATH
    current = context
    for entry in _load_manifest(path):
        module_name = str(entry["module"])
        extension_id = str(entry["extensionId"])
        try:
            module = import_module(module_name)
        except Exception as exc:  # import failures are authority failures, never soft fallback
            raise NNGLAMapExtensionManifestError(
                f"failed to import registered NNGLA map extension {extension_id}"
            ) from exc
        compose = getattr(module, "compose", None)
        if not callable(compose):
            raise NNGLAMapExtensionManifestError(
                f"registered NNGLA map extension {extension_id} does not export compose(context)"
            )
        next_context = compose(current)
        if not isinstance(next_context, NNGLAMapExtensionContext):
            raise NNGLAMapExtensionManifestError(
                f"registered NNGLA map extension {extension_id} returned an invalid context"
            )
        if next_context.pool is not current.pool:
            raise NNGLAMapExtensionManifestError(
                f"registered NNGLA map extension {extension_id} replaced the database pool"
            )
        if next_context.runtime_mode != current.runtime_mode:
            raise NNGLAMapExtensionManifestError(
                f"registered NNGLA map extension {extension_id} changed runtime mode"
            )
        current = next_context
    return current


__all__ = [
    "EXTENSION_MANIFEST_VERSION",
    "EXTENSION_MODULE_PREFIX",
    "NNGLAMapExtensionManifestError",
    "compose_nngla_map_extensions",
]
