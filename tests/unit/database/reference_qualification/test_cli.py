from database.reference_qualification.cli import main


class Cursor:
    def __init__(self): self.rows=[]
    def execute(self, sql, params=None):
        normalized=" ".join(sql.split())
        if "current_database()" in normalized: self.rows=[("npp_dev",)]
        else: self.rows=[]
    def fetchone(self): return self.rows[0]
    def fetchall(self): return list(self.rows)
class Connection:
    def cursor(self): return Cursor()
    def close(self): pass


def test_cli_inspect_schema_uses_short_repository_owned_command(capsys):
    environ={
        "PGHOST":"db.example", "PGPORT":"5432", "PGDATABASE":"npp_dev", "PGUSER":"npp_admin",
        "PGSSLMODE":"require", "PGCONNECT_TIMEOUT":"10", "NPP_ENVIRONMENT":"development",
    }
    code=main(
        ["inspect-schema", "--schema", "reference"],
        environ=environ,
        password_fn=lambda prompt:"secret",
        connection_factory_builder=lambda target,password:(lambda:Connection()),
    )
    assert code==0
    assert "POSTGRESQL REFERENCE SCHEMA QUALIFICATION" in capsys.readouterr().out

def test_cli_lists_catalogue_plans_without_database_writes(capsys):
    environ={"PGHOST":"db.example","PGPORT":"5432","PGDATABASE":"npp_dev","PGUSER":"npp_admin","PGSSLMODE":"require","PGCONNECT_TIMEOUT":"10","NPP_ENVIRONMENT":"development"}
    code=main(["list-catalogue-plans"],environ=environ,password_fn=lambda _:"secret",connection_factory_builder=lambda target,password:(lambda:Connection()))
    assert code==0
    assert "native-core" in capsys.readouterr().out

def test_cli_parser_exposes_catalogue_plan_execution_commands():
    from database.reference_qualification.cli import build_parser
    parser=build_parser()
    for command in ("preview-catalogue-plan","run-catalogue-plan","verify-catalogue-plan"):
        args=parser.parse_args([command,"--plan","native-core","--runtime","simulation"])
        assert args.command==command
