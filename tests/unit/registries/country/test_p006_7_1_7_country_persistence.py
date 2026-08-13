from dataclasses import replace
from pathlib import Path
import pytest
from registries.country.persistence import MemoryCountryRepository,CountryAlreadyExistsError,CountryVersionConflictError
from registries.country.persistence_source import build_country_registry_record
ROOT=Path(__file__).parents[4]
def test_builds_canonical_country_record_from_locked_sources():
 r=build_country_registry_record(ROOT); assert r.country_id=='country:novegeo'; assert r.alpha2_code=='NV'; assert r.alpha3_code=='NVG'; assert r.realm_id=='realm:nexilabs:novegeo'; assert r.currency_code=='NGC'
def test_memory_repository_round_trip_and_duplicate_protection():
 r=build_country_registry_record(ROOT); repo=MemoryCountryRepository(); assert repo.add(r)==r; assert repo.get(r.country_id)==r; assert repo.exists(r.country_id); assert repo.list_all()==(r,)
 with pytest.raises(CountryAlreadyExistsError): repo.add(r)
def test_replace_requires_exact_optimistic_version_increment():
 r=build_country_registry_record(ROOT); repo=MemoryCountryRepository(); repo.add(r); r2=replace(r,identity=replace(r.identity,record_version=2)); assert repo.replace(r2,expected_version=1).record_version==2
 with pytest.raises(CountryVersionConflictError): repo.replace(replace(r2,identity=replace(r2.identity,record_version=3)),expected_version=1)
