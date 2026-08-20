import pytest

from registries.nngla.migration_ready.cli import build_parser


def test_record_commands_require_operator_selected_count_and_support_explicit_start():
    parser = build_parser()
    preview = parser.parse_args(["preview-records", "--count", "500"])
    assert preview.command == "preview-records"
    assert preview.count == 500
    assert preview.start_ordinal is None

    verify = parser.parse_args(["preview-records", "--count", "500", "--start-ordinal", "1"])
    assert verify.start_ordinal == 1

    execute = parser.parse_args(
        [
            "execute-records",
            "--count",
            "800",
            "--fingerprint",
            "f" * 64,
            "--submitter",
            "ASLEKI-DEV",
            "--approver",
            "ASLEKI-ADMIN",
        ]
    )
    assert execute.count == 800


def test_record_preview_count_is_required():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["preview-records"])
