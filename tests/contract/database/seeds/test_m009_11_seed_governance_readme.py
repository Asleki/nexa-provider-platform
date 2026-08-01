from pathlib import Path

README = Path("database/seeds/README.md")


def test_seed_governance_readme_locks_python_owned_import_path():
    text = README.read_text(encoding="utf-8")
    assert "source-specific Python adapter" in text
    assert "Direct SQL imports" in text
    assert "PostgreSQL `COPY`" in text
    assert "Python owns" in text
    assert "runtime mode, name kind, and Python-produced search value" in text


def test_seed_governance_readme_separates_seed_families_and_future_contracts():
    text = README.read_text(encoding="utf-8")
    for value in (
        "name_catalogue/novegeo/",
        "name_catalogue/multicultural/",
        "name_catalogue/immigration/",
        "title_catalogue/",
        "This milestone does not create a Tribe Registry",
        "This milestone does not create a full-name-pair table",
    ):
        assert value in text
