"""Shared paths/helpers for P006.7.11.7.19 Bundle 17O."""
from __future__ import annotations
from csv import DictReader
from pathlib import Path
from registries.nngla.spatial_fabric.bundle17m._shared import normalize_name_text

ROOT=Path(__file__).resolve().parents[4]
SPATIAL_ROOT=ROOT/"data"/"novegeo"/"nngla"/"spatial-fabric"/"source"
CONTROL_ROOT=SPATIAL_ROOT/"02_controlled_codes"
RELATIONSHIP_ROOT=SPATIAL_ROOT/"08_relationships"
QUERY_CATALOGUE_PATH=CONTROL_ROOT/"novegeo_spatial_query_catalogue_v001.csv"
QUERY_RESULT_CONTRACTS_PATH=CONTROL_ROOT/"novegeo_spatial_query_result_contracts_v001.csv"
READ_MODEL_CATALOGUE_PATH=CONTROL_ROOT/"novegeo_read_model_definition_catalogue_v001.csv"
GEOCODING_RULES_PATH=CONTROL_ROOT/"novegeo_geocoding_normalization_rules_v001.csv"
CROSS_REGISTRY_PATH=RELATIONSHIP_ROOT/"novegeo_cross_registry_spatial_reference_contracts_v001.csv"
SCHEMA_PATH=ROOT/"database"/"schemas"/"nngla_spatial_query_read_models.sql"

def csv_rows(path: Path) -> tuple[dict[str,str],...]:
    with Path(path).open("r",encoding="utf-8-sig",newline="") as h:
        return tuple(dict(r) for r in DictReader(h))

__all__=[name for name in globals() if name.isupper() or name in {"csv_rows","normalize_name_text"}]
