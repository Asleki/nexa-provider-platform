from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.api.app.nngla_map_extensions import (
    NNGLAMapExtensionContext,
    NNGLAMapExtensionManifestError,
    compose_nngla_map_extensions,
)


class FakeRepository:
    def __init__(self, runtime_mode: str = "simulation", name: str = "repo") -> None:
        self.runtime_mode = runtime_mode
        self.name = name


class FakeService:
    def __init__(self, repository: FakeRepository, name: str = "service") -> None:
        self.repository = repository
        self.name = name


def context() -> NNGLAMapExtensionContext:
    repository = FakeRepository()
    return NNGLAMapExtensionContext(
        pool=object(),
        runtime_mode="simulation",
        map_repository=repository,
        map_read_service=FakeService(repository),
        resources={"city_public_map_repository": object()},
    )


def write_manifest(path: Path, extensions: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"manifestVersion": 1, "extensions": extensions}), encoding="utf-8")
    return path


def test_empty_manifest_is_identity_composition(tmp_path: Path) -> None:
    initial = context()
    result = compose_nngla_map_extensions(initial, manifest_path=write_manifest(tmp_path / "manifest.json", []))
    assert result is initial
    assert result.map_repository is initial.map_repository
    assert result.map_read_service is initial.map_read_service


def test_extensions_apply_in_manifest_order_and_preserve_pool_runtime(tmp_path: Path) -> None:
    initial = context()
    calls: list[str] = []

    def importer(module_name: str):
        def compose(current: NNGLAMapExtensionContext) -> NNGLAMapExtensionContext:
            calls.append(module_name)
            repository = FakeRepository(current.runtime_mode, name=module_name)
            service = FakeService(repository, name=module_name)
            return current.with_layer(
                map_repository=repository,
                map_read_service=service,
                resources={module_name.rsplit(".", 1)[-1]: object()},
            )

        return SimpleNamespace(compose=compose)

    manifest = write_manifest(
        tmp_path / "manifest.json",
        [
            {
                "extensionId": "nngla-map-extension:municipality:v1",
                "order": 100,
                "module": "infrastructure.api.app.nngla_map_extensions.layers.municipality",
            },
            {
                "extensionId": "nngla-map-extension:city-district:v1",
                "order": 200,
                "module": "infrastructure.api.app.nngla_map_extensions.layers.city_district",
            },
        ],
    )
    result = compose_nngla_map_extensions(initial, manifest_path=manifest, import_module=importer)
    assert calls == [
        "infrastructure.api.app.nngla_map_extensions.layers.municipality",
        "infrastructure.api.app.nngla_map_extensions.layers.city_district",
    ]
    assert result.pool is initial.pool
    assert result.runtime_mode == initial.runtime_mode
    assert result.map_repository.name.endswith("city_district")
    assert "municipality" in result.resources
    assert "city_district" in result.resources
    assert "city_public_map_repository" in result.resources


@pytest.mark.parametrize(
    "extensions",
    [
        [{"extensionId": "bad", "order": 100, "module": "infrastructure.api.app.nngla_map_extensions.layers.x"}],
        [
            {
                "extensionId": "nngla-map-extension:x:v1",
                "order": 100,
                "module": "os.path",
            }
        ],
        [
            {
                "extensionId": "nngla-map-extension:x:v1",
                "order": 200,
                "module": "infrastructure.api.app.nngla_map_extensions.layers.x",
            },
            {
                "extensionId": "nngla-map-extension:y:v1",
                "order": 100,
                "module": "infrastructure.api.app.nngla_map_extensions.layers.y",
            },
        ],
    ],
)
def test_manifest_validation_fails_closed(tmp_path: Path, extensions: list[dict[str, object]]) -> None:
    with pytest.raises(NNGLAMapExtensionManifestError):
        compose_nngla_map_extensions(context(), manifest_path=write_manifest(tmp_path / "manifest.json", extensions))


def test_registered_extension_must_return_context(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "manifest.json",
        [
            {
                "extensionId": "nngla-map-extension:x:v1",
                "order": 100,
                "module": "infrastructure.api.app.nngla_map_extensions.layers.x",
            }
        ],
    )
    with pytest.raises(NNGLAMapExtensionManifestError, match="invalid context"):
        compose_nngla_map_extensions(
            context(),
            manifest_path=manifest,
            import_module=lambda _name: SimpleNamespace(compose=lambda _context: object()),
        )


def test_context_rejects_repository_service_mismatch() -> None:
    first = FakeRepository()
    second = FakeRepository()
    with pytest.raises(ValueError, match="bound to map_repository"):
        NNGLAMapExtensionContext(
            pool=object(),
            runtime_mode="simulation",
            map_repository=first,
            map_read_service=FakeService(second),
        )
