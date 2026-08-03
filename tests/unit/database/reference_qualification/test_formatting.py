from database.reference_qualification.contracts import (
    PostgreSQLSchemaReport,
    ProductionNameQualificationReport,
    QualificationFinding,
)
from database.reference_qualification.formatting import format_production_report, format_schema_report


def test_formatters_include_load_bearing_evidence():
    schema = PostgreSQLSchemaReport("npp_dev", ("reference",), ("reference.canonical_name",), (), (), (), (), ())
    assert "reference.canonical_name" in format_schema_report(schema)

    production = ProductionNameQualificationReport(
        "q1", "name:1", "José", "josé", "first_name", "production",
        "created_new_canonical_name", "reused_existing_canonical_name", 1, 0,
        (QualificationFinding("DUPLICATE_REUSED", "passed", "duplicate reused"),),
    )
    output = format_production_report(production)
    assert "Passed: True" in output
    assert "DUPLICATE_REUSED" in output
