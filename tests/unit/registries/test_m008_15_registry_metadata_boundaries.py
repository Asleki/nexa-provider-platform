from pathlib import Path

def test_m008_15_is_additive_and_preserves_prior_milestones():
    root = Path(__file__).resolve().parents[3]
    registries = root / "registries"
    assert (registries / "metadata").is_dir()
    assert (registries / "core" / "registry_definition.py").is_file()
    assert (root / "tests/unit/registries/test_m008_14_registry_stabilization_boundaries.py").is_file()

def test_m008_15_does_not_implement_future_metadata_repository_or_api():
    root = Path(__file__).resolve().parents[3] / "registries/metadata"
    names = {path.name for path in root.glob("*.py")}
    assert "registry_metadata_repository.py" not in names
    assert "registry_metadata_api.py" not in names
    assert "registry_metadata_event_factory.py" not in names

def test_m008_15_does_not_modify_relationship_foundation_scope():
    root = Path(__file__).resolve().parents[3]
    assert not (root / "registries/metadata/relationship_provenance.py").exists()
