from hashlib import sha256
from pathlib import Path

from registries.nngla.spatial_fabric.bundle17d import (
    artifact_drift_findings,
    bundle17d_is_qualified,
    derive_marine_spatial_qualification_results,
    load_marine_sources,
)
from registries.nngla.spatial_fabric.source_inventory import ROOT


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_bundle17d_closes_new_waters_foundation_without_route_names_or_postgresql_writes():
    data = load_marine_sources()
    rows = derive_marine_spatial_qualification_results()
    assert len(rows) == 49
    assert all(not row["route_name_id"] and not row["canonical_route_name"] for row in data["novegeo_sea_route_candidates_v001.csv"])
    assert data["novegeo_marine_waterbody_vertices_v001.csv"] == ()
    assert artifact_drift_findings() == ()
    assert bundle17d_is_qualified()


def test_bundle17d_does_not_modify_locked_feature_vocabulary_or_new_waters_v001_sources():
    expected = {
        "data/novegeo/nngla/geographic-identity-places/source/02_controlled_codes/feature_type_codes.csv": "f098ab2c5e47287764aca78c0cfa150810e8aecfab7ac821b9c1230c553c0a27",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_island_mainland_connections_v001.csv": "e2a0b22303f94b831320f7d0b6847894b58449c2bc03ae8a7924e3be1be14ce1",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_island_physical_state_v001.csv": "2151946897e7bcc0e850d4435a5eaeb2cfb5e43a1dd27729bdfcc1a0f02bb294",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_marine_coastal_interfaces_v001.csv": "e5b1ec484dc7e9f0bab98c48b2d80cdf602d8ccd3526ad202ab03fef7b685209",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_marine_route_anchor_points_v001.csv": "f0627b9cf3f6ad03e1bf8efe9b6c70ba833c461883041fdc5385414a76710c0b",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_marine_route_validation_v001.csv": "96dd7229e3170c61700dd8ae82d314cb667b107a56be33cd85c3c5ee2489a118",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_marine_waterbodies_v001.csv": "7c0e91cf1aaabc242ef9ad64f7499ca777536805c008a7b3217a961142ddf822",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_marine_waterbody_vertices_v001.csv": "5efcfcadc0c7c28781a4d37a2661749aceb7d5ca4fb21282e632ad8acbd6700a",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_sea_route_candidates_v001.csv": "e8e28bd37f2334caeeea076e8eeaae807c10b9f0b604d833069510eb5469b7e6",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_sea_route_derivation_crosswalk_v001.csv": "3eb108fc84b5444280a4a2ba1c3b06c65856b81b67ce834a67a1c3f08feec751",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_sea_route_name_catalogue_v001.csv": "e7b77f244e638bacdaf9ef91f872471cc7d0005ecec0d23f387f14ec63902d56",
        "data/novegeo/nngla/spatial-fabric/source/05_new_waters_ocean/novegeo_sea_route_vertices_v001.csv": "2aae0932e0c7221552e4f5a5b4d0f90d695bc1f9e61c728025ea3a536df1784a",
    }
    assert {path: _hash(ROOT / path) for path in expected} == expected


def test_bundle17d_does_not_modify_locked_bundle17c_production_files():
    expected = {
        "registries/nngla/spatial_fabric/bundle17c/__init__.py": "cb91853100a35b8a655dda37485c169be25315f4d06ecf39149b7ed6c3dd5889",
        "registries/nngla/spatial_fabric/bundle17c/_shared.py": "18baff601d7b8899f1ee9fb80079f305737debc7f86ace1a7a6e2e8ef60c54d6",
        "registries/nngla/spatial_fabric/bundle17c/artifacts.py": "77766fa24e9f9b9fab04ca07c7c43ea1f2a1279935ea4f0368ae44bceccc9c46",
        "registries/nngla/spatial_fabric/bundle17c/compatibility.py": "9c461796643c2b90906bcaf96fc7780cc7832a685cd2b5a4847c2d61196837b0",
        "registries/nngla/spatial_fabric/bundle17c/conflict_rules.py": "268d5f89703ebe48c26a675008cdaa2dd6e72ed613968be78f72e4a2e1636241",
        "registries/nngla/spatial_fabric/bundle17c/contracts.py": "9a3dae5629b89116e372332a8d537401beb268fbb37610acade1ce010655dbcc",
        "registries/nngla/spatial_fabric/bundle17c/occupancy.py": "dc26c5c1d8ff6dbef008111af9b46f30fc15cb1792240212606561fb1da0f745",
        "registries/nngla/spatial_fabric/bundle17c/qualification.py": "fe22b8808613e886ff04fa0c5905d2141612f7ae51166a8f3f44a16f1a9c7a3e",
        "registries/nngla/spatial_fabric/bundle17c/relationship_types.py": "e570bfc8982af3498efba468a987da8ef2e491fc353518edf5a03c29ec24407a",
    }
    assert {path: _hash(ROOT / path) for path in expected} == expected


def test_bundle17d_does_not_touch_roadmap_or_p006_7_11_database_migrations():
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
    migrations = sorted((ROOT / "database/migrations").glob("m006_07_11*.sql"))
    assert {path.name: _hash(path) for path in migrations} == expected_migrations
