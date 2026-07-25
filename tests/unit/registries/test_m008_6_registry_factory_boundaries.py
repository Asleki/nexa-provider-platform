from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FACTORIES = ROOT / "registries" / "factories"


def _text(name: str) -> str:
    return (FACTORIES / name).read_text(encoding="utf-8")


def test_m008_6_files_exist_in_new_factories_package():
    assert {path.name for path in FACTORIES.glob("*.py")} == {
        "__init__.py",
        "registry_repository_factory.py",
        "registry_repository_registry.py",
        "registry_repository_factory_errors.py",
    }


def test_factory_does_not_implement_later_registry_milestones():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in FACTORIES.glob("*.py"))
    forbidden_imports = (
        "registries.catalogues", "registries.governance", "registries.validators",
        "shared.audit", "shared.events", "fastapi", "flask", "supabase",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in combined


def test_factory_constructs_repositories_not_domain_registry_objects():
    text = _text("registry_repository_factory.py")
    assert "MemoryRegistryRepository" in text
    assert "RegistryDefinition(" not in text
    assert "BaseRegistry(" not in text


def test_ports_do_not_export_factory_symbols():
    ports_init = (ROOT / "registries" / "ports" / "__init__.py").read_text(encoding="utf-8")
    assert "RegistryRepositoryFactory" not in ports_init
    assert "RegistryRepositoryRegistry" not in ports_init


def test_previous_m008_tests_remain_present():
    folder = ROOT / "tests" / "unit" / "registries"
    for number in range(1, 6):
        matches = list(folder.glob(f"test_m008_{number}_*_boundaries.py"))
        assert matches, f"M008.{number} boundary test must remain present"
