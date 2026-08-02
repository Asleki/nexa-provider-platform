from database.migration_control.cli import build_parser
def test_cli_exposes_only_official_commands():
 for cmd in ('status','plan','apply','verify','history'): assert build_parser().parse_args([cmd]).command==cmd
