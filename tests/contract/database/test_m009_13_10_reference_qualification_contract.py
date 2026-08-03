from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_m009_13_10_is_additive_and_does_not_rewrite_locked_migrations():
    package = ROOT / "database" / "reference_qualification"
    expected = {
        "__init__.py", "__main__.py", "cli.py", "contracts.py", "errors.py",
        "formatting.py", "postgresql_inspector.py", "production_name_qualifier.py", "service.py",
    }
    assert expected.issubset({item.name for item in package.iterdir()})
    assert (ROOT / "database" / "migrations" / "m009_10_04_name_catalogue.sql").is_file()
    assert (ROOT / "database" / "migrations" / "m009_12_06_name_authority.sql").is_file()


def test_m009_13_10_cli_exposes_schema_and_production_qualification_commands():
    text=(ROOT / "database" / "reference_qualification" / "cli.py").read_text(encoding="utf-8")
    assert "inspect-schema" in text
    assert "qualify-production-name" in text
    assert "QUALIFY PRODUCTION NAME" in text
