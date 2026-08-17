from registries.nngla.spatial_fabric.bundle17c import CompatibilityOutcome, evaluate_compatibility
from registries.nngla.spatial_fabric.bundle17c.compatibility import compatibility_rules


def test_bundle17c_rules_are_data_driven_and_cover_current_feature_candidates():
    rules = compatibility_rules()
    assert len(rules) == 16
    assert len({row.compatibility_rule_code for row in rules}) == len(rules)
    current = {"MOUNTAIN", "VALLEY", "PLATEAU", "PLAIN", "BAY", "BEACH", "CAPE", "CLIFF", "ESTUARY", "NATURAL_HARBOUR"}
    assert current <= {row.subject_type_code for row in rules}


def test_bundle17c_compatibility_is_fail_closed_for_unknown_rule_or_missing_required_context():
    assert evaluate_compatibility(
        "UNKNOWN", "UNKNOWN", "INTERSECTS", "UNKNOWN", "UNKNOWN", geometry_complete=True,
    ) is CompatibilityOutcome.NOT_EVALUABLE
    assert evaluate_compatibility(
        "CADASTRE", "PARCEL", "OVERLAPS", "CADASTRE", "PARCEL", geometry_complete=True,
    ) is CompatibilityOutcome.BLOCK
    assert evaluate_compatibility(
        "CADASTRE", "PARCEL", "OVERLAPS", "CADASTRE", "PARCEL", geometry_complete=True,
        supplied_contexts=("CADASTRAL_LINEAGE_OPERATION_REQUIRED",),
    ) is CompatibilityOutcome.ALLOW_WITH_CONDITION


def test_bundle17c_missing_geometry_never_silently_passes():
    assert evaluate_compatibility(
        "NATURAL_FEATURE", "MOUNTAIN", "WITHIN", "SOVEREIGN_GROUND", "SOVEREIGN_PART",
        geometry_complete=False,
    ) is CompatibilityOutcome.REVIEW_REQUIRED
