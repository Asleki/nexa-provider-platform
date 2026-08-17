"""Governed runtime command catalogue."""
from __future__ import annotations
from ._shared import COMMAND_CATALOGUE_PATH, csv_rows
from .contracts import CommandDefinition

def command_definitions() -> tuple[CommandDefinition, ...]:
    rows = []
    for row in csv_rows(COMMAND_CATALOGUE_PATH):
        rows.append(CommandDefinition(
            command_code=row["command_code"],
            command_version=int(row["command_version"]),
            domain_code=row["domain_code"],
            target_family=row["target_family"],
            action_code=row["action_code"],
            handler_key=row["handler_key"],
            allowed_runtimes=frozenset(x.strip().lower() for x in row["allowed_runtimes"].split("|") if x.strip()),
            effect_scope_policy=row["effect_scope_policy"],
            identity_allocation_policy=row["identity_allocation_policy"],
            approval_requirement=row["approval_requirement"],
            bulk_policy_code=row["bulk_policy_code"],
            status=row["status"],
        ))
    return tuple(rows)

def command_map() -> dict[str, CommandDefinition]:
    rows = command_definitions()
    result = {row.command_code: row for row in rows}
    if len(result) != len(rows): raise ValueError("duplicate command_code in runtime command catalogue")
    return result

def get_command_definition(command_code: str, command_version: int = 1) -> CommandDefinition:
    item = command_map().get(str(command_code).strip().upper())
    if item is None or item.command_version != command_version or item.status != "ACTIVE":
        raise KeyError(f"unsupported runtime command: {command_code} v{command_version}")
    return item

__all__ = ["command_definitions","command_map","get_command_definition"]
