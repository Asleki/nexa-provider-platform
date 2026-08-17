"""Bundle 17C conflict rule-set metadata."""
from __future__ import annotations


def conflict_rule_set_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        ("NG-CONFLICT-RS-LANDFORM", "Landform ground compatibility", "NATURAL_FEATURE", "NOT_EVALUABLE", "REVIEW_REQUIRED", "PRIORITY_THEN_EXPLICIT_CONTEXT", "false", "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES"),
        ("NG-CONFLICT-RS-COASTAL", "Coastal feature/interface compatibility", "COASTAL", "NOT_EVALUABLE", "REVIEW_REQUIRED", "PRIORITY_THEN_EXPLICIT_CONTEXT", "false", "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES"),
        ("NG-CONFLICT-RS-TRANSPORT", "Transport crossing compatibility", "TRANSPORT", "NOT_EVALUABLE", "REVIEW_REQUIRED", "PRIORITY_THEN_EXPLICIT_CONTEXT", "true", "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES"),
        ("NG-CONFLICT-RS-SETTLEMENT", "Settlement land/marine compatibility", "SETTLEMENT", "NOT_EVALUABLE", "BLOCK", "PRIORITY_THEN_EXPLICIT_CONTEXT", "true", "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES"),
        ("NG-CONFLICT-RS-CADASTRE", "Cadastral non-overlap and lineage context", "CADASTRE", "NOT_EVALUABLE", "BLOCK", "PRIORITY_THEN_EXPLICIT_CONTEXT", "true", "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES"),
    )
    return tuple({
        "conflict_rule_set_code": code,
        "canonical_label": label,
        "rule_scope": scope,
        "applies_to_domain": scope,
        "evaluation_order": str(index),
        "default_no_rule_outcome": default,
        "unresolved_geometry_outcome": unresolved,
        "precedence_policy": precedence,
        "stop_on_block": stop,
        "extension_policy": extension,
        "effective_from": "2026-08-17",
        "status": "ACTIVE",
        "description": label,
    } for index, (code, label, scope, default, unresolved, precedence, stop, extension) in enumerate(definitions, start=1))


__all__ = ["conflict_rule_set_rows"]
