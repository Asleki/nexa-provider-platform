from pathlib import Path
ROOT=Path(__file__).parents[3]

def test_cli_execution_is_additive_and_requires_no_new_migration():
    assert (ROOT/"database/reference_qualification/catalogue_execution/service.py").exists()
    assert not any(p.name.startswith("m009_13_12") for p in (ROOT/"database/migrations").glob("*.sql"))
    cli=(ROOT/"database/reference_qualification/cli.py").read_text()
    assert "preview-catalogue-plan" in cli
    assert "run-catalogue-plan" in cli
    assert "verify-catalogue-plan" in cli
