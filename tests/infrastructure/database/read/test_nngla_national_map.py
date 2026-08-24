from infrastructure.database.read.nngla_national_map import MapBounds, PostgreSQLNNGLANationalMapRepository

ROW=("NG-PLC-000001","PLACE","Alpha","publication:nngla:legacy-or-governed-reference","NG-GEO-000001",1,"PLACE_REFERENCE_POINT","POINT","NG-CRS-EPSG4326",'{"type":"Point","coordinates":[31.0,-18.0]}',"SHARED_REFERENCE","NNGLA_PLACE_TYPE","CITY",2)
class Cursor:
    def __init__(self): self.sql=""; self.params=()
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def execute(self,sql,params=()): self.sql=sql; self.params=params
    def fetchall(self): return [ROW]
class Conn:
    def __init__(self,c): self.c=c
    def cursor(self): return self.c
class Ctx:
    def __init__(self,x): self.x=x
    def __enter__(self): return self.x
    def __exit__(self,*a): return False
class Pool:
    def __init__(self): self.cursor=Cursor(); self.read_only=[]
    def connection(self,read_only=False): self.read_only.append(read_only); return Ctx(Conn(self.cursor))

def test_map_repository_reads_existing_public_projection_without_requiring_later_publication_ledger():
    pool=Pool(); repo=PostgreSQLNNGLANationalMapRepository(pool,runtime_mode="simulation")
    page=repo.list_features(bounds=MapBounds(30,-20,32,-17),families=["PLACE"],limit=10)
    assert page.items[0].subject_id=="NG-PLC-000001"
    assert page.items[0].geometry["type"]=="Point"
    assert "WHERE visibility='PUBLIC'" in pool.cursor.sql
    assert "p.visibility" not in pool.cursor.sql
    assert "p.publication_reference IS NOT NULL" in pool.cursor.sql
    assert "ST_MakeEnvelope" in pool.cursor.sql
    assert "SHARED_REFERENCE" in pool.cursor.sql
    assert "nngla_publication_record" not in pool.cursor.sql
    assert pool.read_only==[True]

def test_map_bounds_reject_inverted_extent():
    import pytest
    with pytest.raises(ValueError): MapBounds(32,-20,30,-17)
