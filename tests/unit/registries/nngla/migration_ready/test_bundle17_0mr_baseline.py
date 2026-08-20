import csv
import json

from registries.nngla.migration_ready.baseline import BOUNDARY_SOURCE_PACKAGE, verify_immutable_baseline
from registries.nngla.migration_ready.candidate_state import ALIGNMENT_PATH
from registries.nngla.migration_ready.catalogue import ROOT


class Cursor:
    def __init__(self, data):
        self.data = data
        self.rows = []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None):
        if "nngla_place_reference" in sql:
            self.rows = list(self.data["PLACE"].items())
        elif "nngla_administrative_area" in sql:
            self.rows = list(self.data["ADMINISTRATIVE_AREA"].items())
        elif "nngla_road" in sql:
            self.rows = list(self.data["ROAD"].items())
        elif "nngla_spatial_feature" in sql:
            self.rows = list(self.data["GEOGRAPHIC_FEATURE"].items())
        elif "nngla_geometry_authority_record" in sql:
            self.rows = list(self.data["EXISTING_GEOMETRY"].items())
        elif "world_boundary" in sql:
            self.rows = [(self.data["BOUNDARY"],)]
        else:
            raise AssertionError(sql)
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0]


class Connection:
    def __init__(self, data): self.data = data
    def cursor(self): return Cursor(self.data)


def _expected_data():
    with (ROOT / ALIGNMENT_PATH).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    key_field = {
        "PLACE": "source_record_id",
        "ADMINISTRATIVE_AREA": "candidate_id",
        "ROAD": "candidate_id",
        "GEOGRAPHIC_FEATURE": "candidate_id",
        "EXISTING_GEOMETRY": "candidate_id",
    }
    data = {family: {} for family in key_field}
    for row in rows:
        data[row["object_family"]][row[key_field[row["object_family"]]]] = row["canonical_id"]
    data["BOUNDARY"] = True
    return data


def test_locked_1284_baseline_and_sovereign_boundary_verify_exactly():
    report = verify_immutable_baseline(ROOT, Connection(_expected_data()))
    assert report.passed
    assert report.expected_count == 1284
    assert report.matched_count == 1284


def test_baseline_identity_mismatch_fails_closed():
    data = _expected_data()
    data["PLACE"]["NGP-000001"] = "NG-PLC-999999"
    report = verify_immutable_baseline(ROOT, Connection(data))
    assert not report.passed
    assert report.conflicts
