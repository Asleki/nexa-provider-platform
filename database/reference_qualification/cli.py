"""Command line entry point for M009.13.10 qualification."""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from uuid import uuid4

from database.migration_control.connection import MigrationDatabaseTarget, build_psycopg_connection_factory
from registries.adapters.postgresql import PostgreSQLConnectionProvider, PostgreSQLNameRepository
from registries.name_authority.manual import ProductionManualNameService
from registries.name_authority.postgresql import PostgreSQLManualNameCandidateRepository

from .contracts import ProductionNameQualificationRequest
from .errors import ReferenceQualificationError
from .formatting import format_json, format_production_report, format_schema_report
from .postgresql_inspector import PostgreSQLReferenceSchemaInspector
from .production_name_qualifier import ProductionNameAuthoringQualifier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m database.reference_qualification")
    parser.add_argument("command", choices=("inspect-schema", "qualify-production-name"))
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--schema", action="append", dest="schemas")
    parser.add_argument("--name")
    parser.add_argument("--kind", default="first_name")
    parser.add_argument("--sex-usage", default="unspecified")
    parser.add_argument("--submitter")
    parser.add_argument("--approver")
    parser.add_argument("--qualification-id")
    parser.add_argument("--origin")
    parser.add_argument("--language")
    parser.add_argument("--community")
    parser.add_argument("--script-code")
    parser.add_argument("--notes")
    parser.add_argument("--yes", action="store_true")
    return parser


def main(argv=None, *, environ=None, input_fn=input, password_fn=getpass.getpass, connection_factory_builder=build_psycopg_connection_factory) -> int:
    args = build_parser().parse_args(argv)
    env = os.environ if environ is None else environ
    try:
        target = MigrationDatabaseTarget.from_environment(env)
        password = password_fn(f"Password for user {target.username}: ")
        factory = connection_factory_builder(target, password)

        if args.command == "inspect-schema":
            result = PostgreSQLReferenceSchemaInspector(factory).inspect(tuple(args.schemas or ("reference", "migration_control")))
            print(format_json(result) if args.format == "json" else format_schema_report(result))
            return 0

        required = {"--name": args.name, "--submitter": args.submitter, "--approver": args.approver}
        missing = [name for name, value in required.items() if not isinstance(value, str) or not value.strip()]
        if missing:
            raise ValueError("missing required arguments: " + ", ".join(missing))
        token = f"QUALIFY PRODUCTION NAME {target.database_name}"
        if not args.yes and input_fn(f"Type {token} to confirm: ").strip() != token:
            raise ValueError("production qualification was not confirmed.")

        provider = PostgreSQLConnectionProvider(factory)
        names = PostgreSQLNameRepository(provider)
        candidates = PostgreSQLManualNameCandidateRepository(provider)
        qualifier = ProductionNameAuthoringQualifier(
            ProductionManualNameService(names, candidates), names, candidates
        )
        request = ProductionNameQualificationRequest(
            raw_name_value=args.name,
            requested_name_kind=args.kind,
            sex_usage=args.sex_usage,
            submitter_actor_id=args.submitter,
            approver_actor_id=args.approver,
            qualification_id=args.qualification_id or uuid4().hex,
            origin_label=args.origin,
            language_label=args.language,
            community_label=args.community,
            script_code=args.script_code,
            notes=args.notes,
        )
        result = qualifier.qualify(request)
        print(format_json(result) if args.format == "json" else format_production_report(result))
        return 0 if result.passed else 2
    except (ReferenceQualificationError, ValueError, TypeError) as exc:
        print(f"REFERENCE_QUALIFICATION_ERROR: {exc}", file=sys.stderr)
        return 1


__all__ = ["build_parser", "main"]
