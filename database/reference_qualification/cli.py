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
from registries.name_authority import ProductionSeedLoader
from registries.name_authority.postgresql import PostgreSQLManualNameCandidateRepository

from .contracts import ProductionNameQualificationRequest
from .errors import ReferenceQualificationError
from .formatting import format_json, format_production_report, format_schema_report
from .postgresql_inspector import PostgreSQLReferenceSchemaInspector
from .production_name_qualifier import ProductionNameAuthoringQualifier
from .development_reset import DevelopmentCatalogueReset
from .reference_bootstrap import GovernedReferenceBootstrap
from registries.reference_authority import PostgreSQLReferenceRepository, PostgreSQLReferenceCodeAllocator, AtomicReferenceCodeAllocator, ReferenceAuthoringService
from registries.name_authority.production_context import PLANS
from registries.name_authority.production_context import PostgreSQLNameContextRepository
from .catalogue_execution import (CataloguePlanExecutionRequest,CataloguePlanPreviewService,GovernedCataloguePlanStepExecutor,CataloguePlanExecutionService,CataloguePlanVerificationService,format_payload,format_preview,format_receipt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m database.reference_qualification")
    parser.add_argument("command", choices=("inspect-schema", "qualify-production-name", "preview-development-reset", "reset-development-catalogue", "bootstrap-reference-catalogues", "list-catalogue-plans", "preview-catalogue-plan", "run-catalogue-plan", "verify-catalogue-plan"))
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
    parser.add_argument("--seed-root", default="database/seeds")
    parser.add_argument("--plan")
    parser.add_argument("--runtime")
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--random-seed", type=int, default=0)
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

        if args.command == "list-catalogue-plans":
            print(format_json({"plans": {key: [step.step_id for step in value.steps] for key, value in PLANS.items()}}))
            return 0

        if args.command in {"preview-catalogue-plan", "run-catalogue-plan", "verify-catalogue-plan"}:
            if not args.plan or not args.runtime:
                raise ValueError("--plan and --runtime are required.")
            request = CataloguePlanExecutionRequest(
                plan_id=args.plan, runtime_mode=args.runtime, sample_size=args.sample_size, random_seed=args.random_seed,
                submitter_actor_id=args.submitter, approver_actor_id=args.approver,
                repository_revision=env.get("NPP_REPOSITORY_REVISION", "unknown"),
            )
            preview_service = CataloguePlanPreviewService(args.seed_root)
            if args.command == "preview-catalogue-plan":
                result = preview_service.preview(request, database_name=target.database_name, environment=target.environment)
                print(format_payload(result) if args.format == "json" else format_preview(result))
                return 0
            provider = PostgreSQLConnectionProvider(factory)
            names = PostgreSQLNameRepository(provider)
            contexts = PostgreSQLNameContextRepository(provider)
            if args.command == "verify-catalogue-plan":
                result = CataloguePlanVerificationService(preview_service, names, contexts).verify(request, database_name=target.database_name, environment=target.environment)
                print(format_json(result))
                return 0 if result["passed"] else 2
            if not args.submitter or not args.approver:
                raise ValueError("--submitter and --approver are required.")
            preview = preview_service.preview(request, database_name=target.database_name, environment=target.environment)
            confirmation = preview.confirmation_token if args.yes else input_fn(f"Type {preview.confirmation_token} to confirm: ").strip()
            executor = GovernedCataloguePlanStepExecutor(ProductionSeedLoader(args.seed_root), names, contexts)
            result = CataloguePlanExecutionService(preview_service, executor).run(request, database_name=target.database_name, environment=target.environment, confirmation=confirmation)
            print(format_payload(result) if args.format == "json" else format_receipt(result))
            return 0 if result.status == "passed" else 2

        if args.command in {"preview-development-reset", "reset-development-catalogue"}:
            reset = DevelopmentCatalogueReset(factory)
            plan = reset.preview(target.database_name, target.environment)
            if args.command == "preview-development-reset":
                print(format_json(plan))
                return 0
            token = f"RESET NAME CATALOGUE {target.database_name} {plan.plan_checksum[:12]}"
            confirmation = token if args.yes else input_fn(f"Type {token} to confirm: ").strip()
            result = reset.execute(plan, confirmation)
            print(format_json(result))
            return 0

        if args.command == "bootstrap-reference-catalogues":
            if not args.submitter or not args.approver:
                raise ValueError("--submitter and --approver are required.")
            token = f"BOOTSTRAP REFERENCE CATALOGUES {target.database_name}"
            if not args.yes and input_fn(f"Type {token} to confirm: ").strip() != token:
                raise ValueError("reference bootstrap was not confirmed.")
            provider = PostgreSQLConnectionProvider(factory)
            repo = PostgreSQLReferenceRepository(provider)
            allocator = AtomicReferenceCodeAllocator(PostgreSQLReferenceCodeAllocator(provider))
            authored = GovernedReferenceBootstrap(ReferenceAuthoringService(repo, allocator), args.seed_root).bootstrap(args.submitter, args.approver)
            created = sum(1 for _, was_created in authored if was_created)
            print(format_json({"processed": len(authored), "created": created, "existing": len(authored)-created}))
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
