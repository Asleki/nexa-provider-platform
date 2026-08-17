"""Data-driven validation for governed runtime commands."""
from __future__ import annotations
from ._shared import VALIDATION_RULES_PATH, csv_rows
from .contracts import RuntimeCommand, ValidationFinding

def validation_rules() -> tuple[dict[str,str], ...]:
    return csv_rows(VALIDATION_RULES_PATH)

def validate_command(command: RuntimeCommand) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    for rule in validation_rules():
        if rule["command_code"] != command.command_code or rule["status"] != "ACTIVE":
            continue
        field = rule["field_name"]
        value = command.payload.get(field)
        kind = rule["rule_type"]
        failed = False
        if kind == "REQUIRED":
            failed = value is None or (isinstance(value, str) and not value.strip())
        elif kind == "POSITIVE_INT":
            failed = isinstance(value, bool) or not isinstance(value, int) or value < 1
        elif kind == "NOT_EQUAL_FIELD":
            other = command.payload.get(rule["rule_value"])
            failed = value is None or other is None or value == other
        else:
            failed = True
        if failed:
            findings.append(ValidationFinding(rule["rule_id"], rule["error_code"], field, rule["message"]))
    return tuple(findings)

__all__ = ["validation_rules","validate_command"]
