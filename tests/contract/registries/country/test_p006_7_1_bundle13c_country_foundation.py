from pathlib import Path
from registries.country.country_foundation_qualification import qualify_novegeo_country_foundation
ROOT=Path(__file__).parents[4]
def test_bundle13c_final_country_foundation_qualification_passes():
 q=qualify_novegeo_country_foundation(ROOT); assert q.status=='PASSED'; assert q.country_id=='country:novegeo'; assert len(q.read_model_checksum)==64; assert 'BUNDLE_13A_QUALIFIED' in q.findings; assert 'BUNDLE_13B_QUALIFIED' in q.findings
def test_bundle13c_does_not_require_frontend_or_live_aws_to_qualify():
 q=qualify_novegeo_country_foundation(ROOT); assert 'POSTGRESQL_ADAPTER_BOUNDARY_RESERVED' in q.findings; assert 'CSV_RUNTIME_AUTHORITY_PROHIBITED' in q.findings
