"""Additive Bundle 17D marine/coastal feature vocabulary."""
from __future__ import annotations

from functools import lru_cache

from registries.nngla.spatial_fabric.source_inventory import ROOT

from ._shared import csv_rows
from .contracts import FeatureTypeExtension

_BASE_FEATURE_TYPES = ROOT / "data/novegeo/nngla/geographic-identity-places/source/02_controlled_codes/feature_type_codes.csv"


@lru_cache(maxsize=1)
def feature_type_extensions() -> tuple[FeatureTypeExtension, ...]:
    values = (
        ("OCEAN", "HYDROLOGY", "Ocean", "POLYGON_OR_MULTIPOLYGON", "Open marine waterbody; outer governed envelope may be absent in source evidence."),
        ("ESTUARY", "COASTAL", "Estuary", "LINESTRING_OR_POLYGON", "Natural coastal transition where riverine and marine systems meet."),
        ("NATURAL_HARBOUR", "COASTAL", "Natural Harbour", "POLYGON", "Naturally sheltered coastal water/shore feature."),
        ("BEACH", "COASTAL", "Beach", "LINESTRING_OR_POLYGON", "Natural shoreline beach feature."),
        ("CLIFF", "COASTAL", "Cliff", "LINESTRING_OR_POLYGON", "Natural steep coastal or terrestrial escarpment feature."),
    )
    return tuple(FeatureTypeExtension(
        feature_type_code=code,
        feature_family_code=family,
        canonical_label=label,
        geometry_expectation=geometry,
        origin_class="NATURAL",
        nngla_recognizable=True,
        nngla_creatable=False,
        nameable=True,
        supports_history=True,
        status="ACTIVE",
        effective_from="2026-08-17",
        effective_to="",
        description=description,
    ) for code, family, label, geometry, description in values)


def effective_feature_type_codes() -> frozenset[str]:
    base = {row["feature_type_code"] for row in csv_rows(_BASE_FEATURE_TYPES)}
    extensions = {row.feature_type_code for row in feature_type_extensions()}
    if base & extensions:
        raise ValueError(f"Bundle 17D feature extension redefines locked type(s): {sorted(base & extensions)}")
    return frozenset(base | extensions)


def feature_type_extension_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "feature_type_code": row.feature_type_code,
        "feature_family_code": row.feature_family_code,
        "canonical_label": row.canonical_label,
        "geometry_expectation": row.geometry_expectation,
        "origin_class": row.origin_class,
        "nngla_recognizable": str(row.nngla_recognizable).lower(),
        "nngla_creatable": str(row.nngla_creatable).lower(),
        "nameable": str(row.nameable).lower(),
        "supports_history": str(row.supports_history).lower(),
        "status": row.status,
        "effective_from": row.effective_from,
        "effective_to": row.effective_to,
        "description": row.description,
    } for row in feature_type_extensions())


__all__ = ["feature_type_extensions", "effective_feature_type_codes", "feature_type_extension_rows"]
