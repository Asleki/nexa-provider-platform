from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def test_town_migration_preserves_non_legal_source_semantics_and_is_fail_closed():
    s=(ROOT/"database/migrations/m006_07_11_nngla_town_settlement_footprint_publication.sql").read_text()
    for token in ("source_contract_match","identity_parentage_match","SETTLEMENT_FOOTPRINT","nngla_town_public_read_v1","QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY"): assert token in s
    assert "f.source_qualification_status='QUALIFIED'" not in s
