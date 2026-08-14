"""Load the governed P006.7 Bundle 15C land-authority source snapshot."""
from __future__ import annotations
from csv import DictReader
from datetime import date
from pathlib import Path
from .cadastre import LandUseDefinition
from .parcels import ParcelRecord
from .tenure import TenureTypeDefinition,TitleTypeDefinition
from .titles import TitleRecord
from .state_land import StateLandCategoryDefinition,StateLandRecord

DEFAULT_SOURCE_ROOT=Path(__file__).resolve().parents[2]/'data'/'novegeo'/'nngla'/'cadastre-titles-state-land'/'source'

def _rows(relative:str,root=DEFAULT_SOURCE_ROOT):
    with (Path(root)/relative).open('r',encoding='utf-8-sig',newline='') as fh:
        return tuple(DictReader(fh))

def _bool(value:str)->bool:
    v=value.strip().lower()
    if v=='true': return True
    if v=='false': return False
    raise ValueError(f'invalid governed boolean {value!r}')

def _date(value:str)->date:
    return date.fromisoformat(value)

def load_land_use_codes(root=DEFAULT_SOURCE_ROOT):
    return tuple(LandUseDefinition(r['land_use_code'],r['canonical_label'],r['category'],_bool(r['allows_mixed_use']),_bool(r['legal_classification']),r['status'],r['description']) for r in _rows('02_controlled_codes/land_use_codes.csv',root))

def load_tenure_types(root=DEFAULT_SOURCE_ROOT):
    return tuple(TenureTypeDefinition(r['tenure_type_code'],r['canonical_label'],r['ownership_model'],r['transferable'].strip().lower(),_bool(r['lease_based']),_bool(r['state_interest_possible']),r['status'],r['description']) for r in _rows('02_controlled_codes/tenure_types.csv',root))

def load_title_types(root=DEFAULT_SOURCE_ROOT):
    return tuple(TitleTypeDefinition(r['title_type_code'],r['canonical_label'],r['tenure_type_code'],_bool(r['registrable']),r['transferable'].strip().lower(),_bool(r['requires_parcel']),r['status'],r['description']) for r in _rows('02_controlled_codes/title_types.csv',root))

def load_state_land_categories(root=DEFAULT_SOURCE_ROOT):
    return tuple(StateLandCategoryDefinition(r['state_land_category_code'],r['canonical_label'],r['purpose'],_bool(r['allocatable']),r['leaseable'].strip().lower(),_bool(r['protected']),r['status'],r['description']) for r in _rows('02_controlled_codes/state_land_categories.csv',root))

def load_parcel_bootstrap(root=DEFAULT_SOURCE_ROOT):
    return tuple(ParcelRecord(r['parcel_id'],r['parent_parcel_id'] or None,r['cadastral_series'],r['parcel_sequence'],r['parcel_status'],r['geometry_reference'] or None,r['land_use_code'] or None,r['survey_status'],_date(r['created_effective_at']),_date(r['retired_effective_at']) if r['retired_effective_at'] else None,r['source_reference']) for r in _rows('07_land/parcel_bootstrap.csv',root))

def load_title_bootstrap(root=DEFAULT_SOURCE_ROOT):
    return tuple(TitleRecord(r['title_id'],r['parcel_id'],r['title_type_code'],r['tenure_type_code'],r['holder_reference'],r['title_status'],_date(r['effective_from']),_date(r['effective_to']) if r['effective_to'] else None,r['source_reference']) for r in _rows('07_land/title_bootstrap.csv',root))

def load_state_land_bootstrap(root=DEFAULT_SOURCE_ROOT):
    return tuple(StateLandRecord(r['state_land_record_id'],r['parcel_id'],r['state_land_category_code'],r['administrative_area_id'] or None,r['status'],_date(r['effective_from']),_date(r['effective_to']) if r['effective_to'] else None,r['source_reference']) for r in _rows('07_land/state_land_bootstrap.csv',root))

__all__=['DEFAULT_SOURCE_ROOT','load_land_use_codes','load_tenure_types','load_title_types','load_state_land_categories','load_parcel_bootstrap','load_title_bootstrap','load_state_land_bootstrap']
