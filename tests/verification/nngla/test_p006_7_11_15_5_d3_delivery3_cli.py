import pytest
from verification.nngla.p006_7_11_15_5.delivery3 import parser


def test_d3_r1_cli_exposes_only_feature_level_primary_commands():
    p = parser()
    help_text = p.format_help()
    # subcommands are registered even if argparse root help is compact
    choices = p._subparsers._group_actions[0].choices
    assert set(choices) == {"qualify-city","adopt-city","publish-city","status"}
    assert "foundation-adopt" not in choices
    assert "adopt-region" not in choices
    assert "publish-cities" not in choices


def test_d3_r1_mutating_commands_require_execute_argument():
    p = parser()
    with pytest.raises(SystemExit):
        p.parse_args(["adopt-city"])
