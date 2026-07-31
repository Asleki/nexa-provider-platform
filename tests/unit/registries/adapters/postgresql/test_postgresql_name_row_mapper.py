from datetime import datetime,timezone
from registries.names import CanonicalName,NameKind,NameMetadata
from registries.adapters.postgresql.postgresql_name_row_mapper import PostgreSQLNameRowMapper as M
def test_round_trip_tuple_row():
    record=CanonicalName("name:first:alex","Alex",NameKind.FIRST_NAME,NameMetadata(created_at=datetime(2026,1,1,tzinfo=timezone.utc),attributes={"name_usage":{"sex_usage":"unisex"}}))
    p=M.parameters(record)
    row=(p[0],p[1],p[3],p[4],p[5],p[6],p[7],p[8],p[9],p[10],p[11],p[12],p[13],p[14])
    restored=M.to_record(row)
    assert restored==record
