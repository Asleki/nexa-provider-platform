from collections import Counter

from registries.nngla.spatial_fabric import derive_coordinate_occurrences
from registries.nngla.spatial_fabric.bundle17b.crs_reconciliation import (
    derive_crs_crosswalk,
    governed_crs_contract,
    qualify_crs_occurrences,
)


def test_locked_novegeo_crs_is_reused_instead_of_creating_a_bundle17b_crs_namespace():
    row = governed_crs_contract()
    assert row["crs_code"] == "NG-CRS-EPSG4326"
    assert row["authority_name"] == "EPSG"
    assert row["authority_code"] == "4326"
    assert row["axis_order"] == "LONGITUDE_LATITUDE"


def test_all_27_coordinate_bearing_source_files_have_explicit_evidence_based_crs_reconciliation():
    rows = derive_crs_crosswalk()
    assert len(rows) == 27
    assert Counter(row.source_crs_form for row in rows) == Counter({"UNDECLARED_IN_ROW": 24, "EPSG:4326": 3})
    assert all(row.governed_crs_code == "NG-CRS-EPSG4326" for row in rows)
    assert all(row.evidence_reference for row in rows)
    assert qualify_crs_occurrences() == ()


def test_undeclared_in_row_is_preserved_as_source_fact_and_reconciled_by_lineage_not_global_rewrite():
    occurrences = derive_coordinate_occurrences()
    assert Counter(item.crs_source_code for item in occurrences) == Counter({
        "UNDECLARED_IN_ROW": 4183,
        "EPSG:4326": 1139,
    })
    crosswalk = {row.source_file_id: row for row in derive_crs_crosswalk()}
    assert crosswalk["NG-SPFILE-001"].source_crs_form == "UNDECLARED_IN_ROW"
    assert crosswalk["NG-SPFILE-001"].reconciliation_basis == "SOURCE_CLIMATE_LINEAGE"
