from pathlib import Path

def test_bundle_c_files_and_cli_commands_exist():
    root=Path(__file__).resolve().parents[3]
    for name in ('drift.py','recovery.py','rollback.py','qualification.py','legacy_cleanup.py','receipts.py','sanitization.py'):
        assert (root/'database'/'migration_control'/name).is_file()
    cli=(root/'database'/'migration_control'/'cli.py').read_text()
    for command in ('inspect-target','prepare-development-target','qualify'):
        assert command in cli
