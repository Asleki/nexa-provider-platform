from pathlib import Path
from registries.country.persistence_source import build_country_registry_record
from registries.country.read_model import CountryReadModelProjector,MemoryCountryReadRepository
ROOT=Path(__file__).parents[4]
def test_projection_preserves_stable_sovereign_references():
 r=build_country_registry_record(ROOT); m=CountryReadModelProjector().project(r); assert m.country_id=='country:novegeo'; assert m.alpha2_code=='NV'; assert m.boundary_id=='boundary:novegeo:sovereign'; assert m.realm_id=='realm:nexilabs:novegeo'; assert m.currency_symbol=='₦G'
def test_semantic_projection_checksum_is_deterministic():
 r=build_country_registry_record(ROOT); p=CountryReadModelProjector(); assert p.project(r).checksum==p.project(r).checksum
def test_read_repository_is_derived_and_rebuildable():
 r=build_country_registry_record(ROOT); repo=MemoryCountryReadRepository(); receipts=CountryReadModelProjector().rebuild((r,),repo,read_model_version=2); assert len(receipts)==1; assert repo.get(r.country_id).read_model_version==2; assert receipts[0].source_record_version==1
