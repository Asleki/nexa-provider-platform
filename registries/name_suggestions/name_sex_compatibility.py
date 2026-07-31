"""Evaluate person sex against canonical-name usage metadata."""
from __future__ import annotations
from registries.names import CanonicalName
from registries.names.person_sex import PersonSex
from registries.names.name_sex_usage import NameSexUsage
from registries.names.name_sex_usage_metadata import read_name_sex_usage
from .name_sex_compatibility_outcome import NameSexCompatibilityOutcome as O
from .name_sex_compatibility_result import NameSexCompatibilityResult

def evaluate_name_sex_compatibility(person_sex:PersonSex|str,name:CanonicalName)->NameSexCompatibilityResult:
    if not isinstance(name,CanonicalName): raise TypeError("name must be CanonicalName.")
    sex=PersonSex.parse(person_sex); usage=read_name_sex_usage(name.metadata)
    if sex is PersonSex.UNSPECIFIED or usage is NameSexUsage.UNSPECIFIED: outcome=O.UNSPECIFIED
    elif usage is NameSexUsage.UNISEX: outcome=O.COMPATIBLE
    elif sex is PersonSex.INTERSEX: outcome=O.AMBIGUOUS
    elif sex.value==usage.value: outcome=O.COMPATIBLE
    else: outcome=O.CONFLICT
    return NameSexCompatibilityResult(sex,usage,outcome,name.name_id)
__all__=["evaluate_name_sex_compatibility"]
