import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PRODUCTION=ROOT/"registries"/"canonical"
TESTS=ROOT/"tests"/"unit"/"registries"/"canonical"
def test_required_production_files_exist():
    assert {"__init__.py","canonical_dataset_type.py","canonical_dataset_reference.py","canonical_dataset_definition.py","canonical_dataset_rules.py"} <= {p.name for p in PRODUCTION.glob("*.py")}
def test_all_new_test_families_exist_without_replacing_old_tests():
    assert {"test_canonical_dataset_type.py","test_canonical_dataset_reference.py","test_canonical_dataset_definition.py","test_canonical_dataset_rules.py","test_canonical_dataset_exports.py"} <= {p.name for p in TESTS.glob("test_*.py")}
def test_future_engines_remain_absent():
    forbidden={"canonical_dataset_repository.py","canonical_merge_engine.py","duplicate_detection_engine.py","dataset_storage.py","dataset_event_factory.py","name_resolution_engine.py"}
    assert not forbidden & {p.name for p in PRODUCTION.glob("*.py")}
def test_package_is_framework_and_storage_neutral():
    forbidden={"fastapi","flask","django","sqlalchemy","supabase","psycopg","requests","httpx"}; imported=set()
    for path in PRODUCTION.glob("*.py"):
        tree=ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imported.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module.split('.')[0])
    assert not forbidden & imported
def test_contract_does_not_embed_domain_specific_name_or_team_fields():
    source=(PRODUCTION/"canonical_dataset_definition.py").read_text()
    for field in ("legal_name:","preferred_name:","team_name:","tournament_name:","bank_account:"):
        assert field not in source
