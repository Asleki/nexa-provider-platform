from pathlib import Path
import csv

from registries.nngla.foundation_qualification import qualify_nngla_foundation

ROOT = Path(__file__).resolve().parents[4]


def test_p006_7_2_foundation_qualifies_all_three_bundles_without_claiming_db_migration():
    receipt = qualify_nngla_foundation(ROOT)
    assert receipt.qualification_id == "qualification:novegeo:nngla-foundation:v1"
    assert receipt.status == "PASSED"
    assert receipt.authority_id == "authority:nngla"
    assert receipt.country_id == "country:novegeo"
    assert receipt.realm_id == "realm:nexilabs:novegeo"
    assert "POSTGIS_SCHEMA_FOUNDATION_QUALIFIED" in receipt.findings
    assert "CONTROLLED_DATABASE_MIGRATION_NOT_EXECUTED" in receipt.findings
    assert "NNGLA_EVENT_AUDIT_LINKED" in receipt.findings
    assert "SECURITY_SENSITIVE_PUBLICATION_BLOCKED" in receipt.findings
    assert len(receipt.publication_content_sha256) == 64


def test_historical_audit_snapshot_remains_source_evidence_and_explicitly_says_not_executed():
    path = ROOT / "data/novegeo/nngla/qualification-foundation/source/novegeo_immutable_audit_event.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    migration = [row for row in rows if row["event_type"] == "DATABASE_MIGRATION_STATUS"]
    assert len(migration) == 1
    assert migration[0]["result"] == "NOT_EXECUTED"
    assert "no database writes performed" in migration[0]["details"]


def test_qualification_is_repeatable_at_contract_level():
    first = qualify_nngla_foundation(ROOT)
    second = qualify_nngla_foundation(ROOT)
    assert first.qualification_id == second.qualification_id
    assert first.status == second.status
    assert first.findings == second.findings
