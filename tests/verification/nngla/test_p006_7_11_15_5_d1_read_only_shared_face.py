import json
from pathlib import Path

from verification.nngla.p006_7_11_15_5.shared_face_preview import main,parser


def test_delivery1_cli_is_explicitly_read_only_and_emits_governance_template(tmp_path):
    output=tmp_path/"preview.json";template=tmp_path/"decisions.json"
    code=main(["--root","NG-PLC-000086","--output",str(output),"--decision-template",str(template)])
    assert code==2
    payload=json.loads(output.read_text())
    assert payload["writeCapability"]=="NONE"
    assert payload["canonicalDatabaseMutation"] is False
    decisions=json.loads(template.read_text())
    assert decisions["faceDecisions"]
    assert "not authority" in decisions["notice"].lower()


def test_delivery1_cli_material_city_parent_rule_escalates_silvermere_to_region_scope(tmp_path):
    output=tmp_path/"silvermere.json"
    code=main([
        "--root","NG-PLC-000258",
        "--material-rule","CITY_PARENT_CONTAINMENT_FAILED",
        "--output",str(output),
    ])
    assert code==2
    payload=json.loads(output.read_text())
    assert payload["scope"]["parentAdministrativeAreaId"]=="NG-ADM-000004"
    assert payload["scope"]["level"]=="REGION_LOCAL_AREAS"


def test_delivery1_cli_has_no_execute_flag_or_database_credentials():
    args=parser().parse_args(["--root","NG-PLC-000086"])
    assert not hasattr(args,"execute")
    body=Path("verification/nngla/p006_7_11_15_5/shared_face_preview.py").read_text()
    for prohibited in ("psycopg","PGPASSWORD","reserve_geometry","persist_geometry","roadmap_frontend"):
        assert prohibited not in body
