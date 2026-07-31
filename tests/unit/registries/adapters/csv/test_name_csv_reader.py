import pytest
from registries.adapters.csv.name_csv_errors import NameCsvHeaderError,NameCsvRowError
from registries.adapters.csv.name_csv_reader import NameCsvReader

def test_reads_unicode_rows_and_tracks_source_line():
    rows=NameCsvReader().read_text("name,name_kind,sex_usage\nTapiwa,first_name,unisex\nŽiva,first_name,female\n")
    assert [r.row_number for r in rows]==[2,3]
    assert rows[1].get("name")=="Živa"

def test_rejects_missing_and_duplicate_headers():
    with pytest.raises(NameCsvHeaderError): NameCsvReader().read_text("name\nAlex\n")
    with pytest.raises(NameCsvHeaderError): NameCsvReader().read_text("name,name,name_kind\nA,B,first_name\n")

def test_rejects_unknown_headers_by_default_but_can_allow_them():
    text="name,name_kind,phone\nAlex,first_name,123\n"
    with pytest.raises(NameCsvHeaderError): NameCsvReader().read_text(text)
    assert NameCsvReader(allow_unknown_columns=True).read_text(text)[0].get("phone")=="123"

def test_rejects_extra_values_and_skips_blank_rows():
    with pytest.raises(NameCsvRowError): NameCsvReader().read_text("name,name_kind\nAlex,first_name,extra\n")
    assert NameCsvReader().read_text("name,name_kind\n,\nAlex,first_name\n")[0].row_number==3
