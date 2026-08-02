"""Run the M009.11.A read-only AWS PostgreSQL qualification."""

from __future__ import annotations

import os
import sys

from registries.adapters.postgresql.postgresql_live_qualification import (
    PostgreSQLLiveQualifier,
    PostgreSQLQualificationConfig,
    load_psycopg_connect,
    render_error_report,
    render_success_report,
)


def main() -> int:
    try:
        config = PostgreSQLQualificationConfig.from_environment(os.environ)
        qualifier = PostgreSQLLiveQualifier(load_psycopg_connect())
        result = qualifier.qualify(config)
        print(render_success_report(config, result))
        return 0
    except Exception as exc:
        print(render_error_report(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
