"""Authorization intersection: foundation authority × command policy × principal."""
from __future__ import annotations
from ._shared import COMMAND_AUTHORIZATION_PATH, FOUNDATION_AUTHORITY_MATRIX_PATH, bool_text, csv_rows
from .contracts import AuthorizationDecision, RuntimeCommand, RuntimePrincipal
from .command_catalogue import get_command_definition

def authorization_rows() -> tuple[dict[str,str], ...]:
    return csv_rows(COMMAND_AUTHORIZATION_PATH)

def _foundation_row(record_family: str, runtime_code: str) -> dict[str,str] | None:
    for row in csv_rows(FOUNDATION_AUTHORITY_MATRIX_PATH):
        if row["authority_code"] == "NNGLA" and row["record_family"] == record_family and row["runtime_code"].lower() == runtime_code.lower() and row["status"] == "ACTIVE":
            return row
    return None

def authorize(command: RuntimeCommand, principal: RuntimePrincipal, *, approval_granted: bool = False) -> AuthorizationDecision:
    definition = get_command_definition(command.command_code, command.command_version)
    reasons: list[str] = []
    runtime = command.runtime_mode.value
    if principal.principal_id != command.principal_id: reasons.append("PRINCIPAL_MISMATCH")
    if principal.runtime_mode is not command.runtime_mode: reasons.append("SESSION_RUNTIME_MISMATCH")
    if runtime not in definition.allowed_runtimes: reasons.append("COMMAND_RUNTIME_NOT_ALLOWED")
    foundation = _foundation_row(definition.target_family, runtime.upper())
    if foundation is None:
        reasons.append("FOUNDATION_AUTHORITY_MISSING")
    elif foundation["effect_scope_code"] != command.effect_scope:
        reasons.append("EFFECT_SCOPE_NOT_AUTHORIZED")
    matched = [
        row for row in authorization_rows()
        if row["command_code"] == definition.command_code
        and row["runtime_code"].lower() == runtime
        and row["status"] == "ACTIVE"
    ]
    if len(matched) != 1:
        reasons.append("COMMAND_AUTHORIZATION_RULE_MISSING")
    else:
        row = matched[0]
        permission = row["required_permission"]
        if permission not in principal.permissions: reasons.append("REQUIRED_PERMISSION_MISSING")
        if row["allowed_effect_scope"] != command.effect_scope: reasons.append("COMMAND_EFFECT_SCOPE_MISMATCH")
        approval_required = bool_text(row["approval_required"]) or (foundation is not None and bool_text(foundation["approval_required"]))
        if approval_required and not approval_granted: reasons.append("APPROVAL_REQUIRED")
    return AuthorizationDecision(not reasons, tuple(reasons))

__all__ = ["authorization_rows","authorize"]
