"""Build canonical persistence records from locked Bundle 13A/13B sources."""
from pathlib import Path
from .qualification import qualify_bundle13a_source
from .bundle13b_qualification import qualify_bundle13b_source
from .persistence import CountryRegistryRecord

def build_country_registry_record(repository_root: str|Path) -> CountryRegistryRecord:
    a=qualify_bundle13a_source(repository_root); b=qualify_bundle13b_source(repository_root)
    return CountryRegistryRecord(identity=a.country.identity,alpha2_code=a.country.alpha2.code_value,alpha3_code=a.country.alpha3.code_value,boundary_id=a.boundary.boundary_id,boundary_version=a.boundary.boundary_version,realm_id=b.source.realm.realm_id,timezone_code=b.source.timezone.timezone_code,calendar_code=b.source.calendar.calendar_code.value,date_time_policy_id=b.source.date_time_policy.policy_id,currency_code=b.source.currency.currency_code,currency_symbol=b.source.currency.currency_symbol)
__all__=["build_country_registry_record"]
