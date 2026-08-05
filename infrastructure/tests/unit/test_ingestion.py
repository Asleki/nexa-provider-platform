from infrastructure.ingestion import DatasetIngestionPipeline
from infrastructure.ingestion.csv import CSVSourceReader
from infrastructure.ingestion.geojson import GeoJSONSourceReader
def pipeline(): return DatasetIngestionPipeline((CSVSourceReader(),GeoJSONSourceReader()))
def test_csv_ingestion_is_deterministic_for_fixed_run_id():
    data=b"dataset_id,title\ndataset:one,One\n"
    a=pipeline().ingest(source_package_id="source:p",source_file_id="source:f",filename="a.csv",media_type="text/csv",data=data,ingestion_run_id="ingestion:1")
    b=pipeline().ingest(source_package_id="source:p",source_file_id="source:f",filename="a.csv",media_type="text/csv",data=data,ingestion_run_id="ingestion:1")
    assert a.receipt_sha256==b.receipt_sha256 and len(a.candidates)==1
def test_geojson_feature_collection_is_parsed():
    data=b'{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"id":"x"},"geometry":null}]}'
    r=pipeline().ingest(source_package_id="source:p",source_file_id="source:g",filename="a.geojson",media_type="application/geo+json",data=data)
    assert len(r.candidates)==1 and not r.rejected
def test_malformed_source_is_rejected_not_written():
    r=pipeline().ingest(source_package_id="source:p",source_file_id="source:g",filename="a.geojson",media_type="application/geo+json",data=b'{}')
    assert not r.candidates and r.rejected[0].code=="SOURCE_PARSE_FAILED"
