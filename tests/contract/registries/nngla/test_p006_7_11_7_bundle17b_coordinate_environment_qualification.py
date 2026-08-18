from collections import Counter
from hashlib import sha256

from registries.nngla.spatial_fabric.bundle17b import (
    bundle17b_is_qualified,
    derive_containment_qualifications,
    derive_crs_crosswalk,
    derive_environment_bindings,
    derive_precision_qualifications,
    derive_source_fidelity_results,
)
from registries.nngla.spatial_fabric.source_inventory import ROOT


def test_bundle17b_closes_coordinate_and_environment_qualification_without_postgresql_writes():
    assert len(derive_crs_crosswalk()) == 27
    assert len(derive_precision_qualifications()) == 10644
    containment = derive_containment_qualifications()
    assert len(containment) == 2411
    assert Counter(row.sovereign_land_relation.value for row in containment) == Counter({
        "INSIDE_SOVEREIGN_LAND": 1348,
        "ON_SOVEREIGN_BOUNDARY": 1048,
        "OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE": 15,
    })
    assert len(derive_source_fidelity_results()) == 5322
    assert len(derive_environment_bindings()) == 1104
    assert bundle17b_is_qualified()


def test_bundle17b_does_not_modify_locked_bundle17a_production_files():
    expected = {
        "__init__.py": "61f19277137be497821ae9db8a910a6db9f083fa62363bcfece5fc879c3f305b",
        "artifacts.py": "79419ed33373602c253297cce92969eee2f6ac997a8fb8c96d3ce220aa836b3a",
        "contracts.py": "6ff09f5fca1d55158e81eb71479278971e820e36fcf8e67ffc08453dabf88ad8",
        "coordinate_occurrences.py": "f36492b935c17fed7a2fc96a164fabe9d593e3d5ed1e2a839dafdd093f371706",
        "qualification.py": "a316db6c7df2354318d4763353b43b2d974d7bafca22f8090d83ea132e21ae39",
        "source_inventory.py": "05699302d2fbc842378045a14220cccd17b788e2e68a76b2a344289cd95f6e82",
        "topology.py": "11ac949be870aac0a8c870bdfdef9e8e0a35cd2e8a2851b816ea79a1f25dc5f3",
    }
    folder = ROOT / "registries/nngla/spatial_fabric"
    actual = {name: sha256((folder / name).read_bytes()).hexdigest() for name in expected}
    assert actual == expected


def test_bundle17b_does_not_add_or_modify_p006_7_11_database_migrations():
    expected = {
        "m006_07_11_nngla_cadastre_runtime.sql": "0289f9fe505cc30b52ddd284b6554d44bc049e18283004e5aea39bb595721c17",
        "m006_07_11_nngla_execution_foundation.sql": "311d349c5fb70ffae466f62281fbe226acd570ae8743d0c3e7ffc2d5640c4c3a",
        "m006_07_11_nngla_identity_places_runtime.sql": "8662852edc2c0ea782c1ab3dc141eea5faddeb82bc4bbb2e5317b61f206a72bb",
        "m006_07_11_nngla_execution_foundation_rollback.sql": "9999de9cac66c819d5cfe390d127739b345e59a8a9e10bd3b36af1e0a8f5fbba",
        "m006_07_11_nngla_geometry_roads_runtime_rollback.sql": "b62cfa2325c9eb04d87f3ca77fe809379e602ad7731df3c8aae37a39917ef14a",
        "m006_07_11_nngla_identity_places_runtime_rollback.sql": "ba692e21f950effee90dd6342e1b4d7f9b769cc603fa094f16af6cd81011b26d",
        "m006_07_11_nngla_geometry_roads_runtime.sql": "bbc847ff4f9fa0fcc73c4be0beb4a5c4bab12e0b67bb394a7f4deed47d6867e9",
        "m006_07_11_nngla_cadastre_runtime_rollback.sql": "bc0135037db52601dd4c7af58fb002051d358154dd940510ecd7cdb1bcde03fd",
    }
    migration_root = ROOT / "database/migrations"
    actual = {name: sha256((migration_root / name).read_bytes()).hexdigest() for name in expected}
    assert actual == expected
