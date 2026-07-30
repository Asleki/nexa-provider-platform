import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
PROD=ROOT/"registries"/"names"
TESTS=ROOT/"tests"/"unit"/"registries"/"names"

def test_m009_1_files_exist_and_old_tests_are_not_replaced():
    required={"__init__.py","canonical_name.py","first_name.py","middle_name.py","surname.py","name_kind.py","name_status.py","name_metadata.py","name_repository.py","name_repository_errors.py","memory_name_repository.py","name_search_query.py","name_search_result.py","name_search_service.py"}
    assert required <= {p.name for p in PROD.glob("*.py")}
    assert len(list(TESTS.glob("test_*.py")))>=14

def test_package_is_storage_framework_and_identity_neutral():
    forbidden={"boto3","psycopg","sqlalchemy","supabase","azure","fastapi","flask","django"}; imported=set(); source=""
    for path in PROD.glob("*.py"):
        text=path.read_text(); source+=text
        tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imported.update(n.name.split('.')[0] for n in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module.split('.')[0])
    assert not forbidden & imported
    for embedded in ("citizen_id:","bank_account:","phone_number:","email_address:","student_id:"):
        assert embedded not in source

def test_suggestion_and_assignment_engines_are_deferred():
    forbidden={"name_suggestion_engine.py","name_assignment.py","citizen_name_generator.py","email_candidate_generator.py"}
    assert not forbidden & {p.name for p in PROD.glob("*.py")}
