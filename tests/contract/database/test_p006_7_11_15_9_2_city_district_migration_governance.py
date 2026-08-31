from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

MIGRATION = (
    ROOT
    / "database/migrations/"
      "m006_07_11_nngla_city_district_spatial_publication.sql"
)


def test_city_district_migration_uses_exact_topology():
    sql = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert (
        "ST_Equals(g.district_union,c.geometry) "
        "AS union_equals_city"
        in sql
    )

    assert (
        "AND sibling_positive_overlap_m2=0 "
        "AND union_equals_city"
        in sql
    )

    assert (
        "nngla_city_district_partition_exact_read_v1"
        in sql
    )

    assert (
        "x.union_equals_city"
        in sql
    )


def test_symmetric_difference_is_diagnostic_not_pass_predicate():
    sql = MIGRATION.read_text(
        encoding="utf-8"
    )

    assert (
        "symmetric_difference_m2"
        in sql
    )

    assert (
        "ST_SymDifference"
        in sql
    )
