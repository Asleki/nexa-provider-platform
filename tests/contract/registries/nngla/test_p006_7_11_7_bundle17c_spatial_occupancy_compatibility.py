from hashlib import sha256
from pathlib import Path

from registries.nngla.spatial_fabric.bundle17c import (
    artifact_drift_findings,
    bundle17c_is_qualified,
    derive_conflict_qualification_results,
    derive_occupancy_relationships,
)
from registries.nngla.spatial_fabric.source_inventory import ROOT


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_bundle17c_closes_reusable_occupancy_without_canonical_database_writes():
    assert len(derive_occupancy_relationships()) == 34
    assert len(derive_conflict_qualification_results()) == 34
    assert artifact_drift_findings() == ()
    assert bundle17c_is_qualified()


def test_bundle17c_does_not_modify_locked_bundle17a_or_bundle17b_production_files():
    expected = {
        "registries/nngla/spatial_fabric/__init__.py": "61f19277137be497821ae9db8a910a6db9f083fa62363bcfece5fc879c3f305b",
        "registries/nngla/spatial_fabric/artifacts.py": "79419ed33373602c253297cce92969eee2f6ac997a8fb8c96d3ce220aa836b3a",
        "registries/nngla/spatial_fabric/contracts.py": "6ff09f5fca1d55158e81eb71479278971e820e36fcf8e67ffc08453dabf88ad8",
        "registries/nngla/spatial_fabric/coordinate_occurrences.py": "f36492b935c17fed7a2fc96a164fabe9d593e3d5ed1e2a839dafdd093f371706",
        "registries/nngla/spatial_fabric/qualification.py": "a316db6c7df2354318d4763353b43b2d974d7bafca22f8090d83ea132e21ae39",
        "registries/nngla/spatial_fabric/source_inventory.py": "05699302d2fbc842378045a14220cccd17b788e2e68a76b2a344289cd95f6e82",
        "registries/nngla/spatial_fabric/topology.py": "11ac949be870aac0a8c870bdfdef9e8e0a35cd2e8a2851b816ea79a1f25dc5f3",
        "registries/nngla/spatial_fabric/bundle17b/__init__.py": "881780d77ab8d73969731864191c3d6c36cc16d9fb21858a7f3f5c236c79984e",
        "registries/nngla/spatial_fabric/bundle17b/_shared.py": "2f1d4f98bd6af84549a7abef5f99241f564b6ad946e0078aae79974220e87a27",
        "registries/nngla/spatial_fabric/bundle17b/artifacts.py": "b8b22a8a8f0ee3a545a1177c55e7eb2077202b3e45e1e06ae5429d3c353a28e4",
        "registries/nngla/spatial_fabric/bundle17b/containment.py": "6c17cc82598f2d1f6f10ccf0c6df62547e3c01cc44ca3018fd753719cbabcdb9",
        "registries/nngla/spatial_fabric/bundle17b/contracts.py": "8912bbc84186cde5f6c66b4420e8155c90f3bbdcd37820ee31f78d020267a409",
        "registries/nngla/spatial_fabric/bundle17b/crs_reconciliation.py": "d227bec8f92ba50437e68d1a1ec93ce33b3eb06560937eef6928410b0cbf1db5",
        "registries/nngla/spatial_fabric/bundle17b/environment_binding.py": "6e3dd691b1733531bf196e4bed6b1bc0a0e0b99f196bda5015fec34249e95ebf",
        "registries/nngla/spatial_fabric/bundle17b/environment_policy.py": "928223c4881d8b12854603e7e6bc6667c42ab6eb6d8cc7b842c28c34e7687f10",
        "registries/nngla/spatial_fabric/bundle17b/precision.py": "d626e6928dd2eb38b4a781afe6bdcc646c4de471be0547ec65ffd490432bfd61",
        "registries/nngla/spatial_fabric/bundle17b/qualification.py": "f9f741ca1d32f492ec015b5cfdfdd834bf92dcd884d8a98411ff41f0be885b65",
        "registries/nngla/spatial_fabric/bundle17b/source_fidelity.py": "5ba205c3eb8c5fa1cdc17599b00d187b0bb54759f40feda46091a316c3c18ef0",
    }
    assert {path: _hash(ROOT / path) for path in expected} == expected


def test_bundle17c_does_not_touch_roadmap_or_p006_7_11_database_migrations():
    roadmap_expected = {
        "roadmap_frontend.py": "00aaeda6241d668710c9a773e726e588d5b7e14ca939caecdff3c5df25cec82e",
        "pwa_roadmap_data.py": "0e466f194faa7aa81334c4d876d6953da35f0df5c22e567981d7c1243f4afb69",
        "PWA_ROADMAP.md": "29b58acadb189bad3c88f89c578f5bb28017bef816ef519232fb817dc65dec40",
    }
    assert {path: _hash(ROOT / path) for path in roadmap_expected} == roadmap_expected
    expected_migrations = {
        "m006_07_11_nngla_cadastre_runtime.sql": "0289f9fe505cc30b52ddd284b6554d44bc049e18283004e5aea39bb595721c17",
        "m006_07_11_nngla_cadastre_runtime_rollback.sql": "bc0135037db52601dd4c7af58fb002051d358154dd940510ecd7cdb1bcde03fd",
        "m006_07_11_nngla_execution_foundation.sql": "311d349c5fb70ffae466f62281fbe226acd570ae8743d0c3e7ffc2d5640c4c3a",
        "m006_07_11_nngla_execution_foundation_rollback.sql": "9999de9cac66c819d5cfe390d127739b345e59a8a9e10bd3b36af1e0a8f5fbba",
        "m006_07_11_nngla_geometry_roads_runtime.sql": "bbc847ff4f9fa0fcc73c4be0beb4a5c4bab12e0b67bb394a7f4deed47d6867e9",
        "m006_07_11_nngla_geometry_roads_runtime_rollback.sql": "b62cfa2325c9eb04d87f3ca77fe809379e602ad7731df3c8aae37a39917ef14a",
        "m006_07_11_nngla_identity_places_runtime.sql": "8662852edc2c0ea782c1ab3dc141eea5faddeb82bc4bbb2e5317b61f206a72bb",
        "m006_07_11_nngla_identity_places_runtime_rollback.sql": "ba692e21f950effee90dd6342e1b4d7f9b769cc603fa094f16af6cd81011b26d",
    }
    migration_root = ROOT / "database/migrations"
    assert {name: _hash(migration_root / name) for name in expected_migrations} == expected_migrations
