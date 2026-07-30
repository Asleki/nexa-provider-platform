from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[4] / "registries" / "name_suggestions"
NEW_FILES = (
    "suggestion_name_normalizer.py",
    "suggestion_duplicate_control.py",
    "suggestion_api.py",
)


def test_completion_modules_remain_storage_framework_and_domain_neutral():
    forbidden = (
        "boto3", "psycopg", "sqlalchemy", "supabase", "fastapi", "flask",
        "django", "citizen", "national_id", "email_candidate", "nexapos", "random",
    )
    combined = "\n".join((PACKAGE / name).read_text(encoding="utf-8").lower() for name in NEW_FILES)
    for token in forbidden:
        assert token not in combined


def test_locked_m009_2_1_to_m009_2_5_files_remain_present_and_new_tests_are_appended():
    locked = (
        "manual_name_entry.py", "single_name_suggestion.py", "pair_name_suggestion.py",
        "trio_name_suggestion.py", "full_name_suggestion.py",
    )
    assert all((PACKAGE / name).exists() for name in locked)
    test_dir = Path(__file__).parent
    assert (test_dir / "test_single_name_suggestion_service.py").exists()
    assert (test_dir / "test_suggestion_api.py").exists()
