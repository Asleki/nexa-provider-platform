from hashlib import sha256
from pathlib import Path
from registries.nngla.source_dataset import *


def test_dataset_manifest_preserves_populated_and_empty_register_semantics():
    populated=SourceDatasetManifestEntry("CAT-1","x","a.csv",2,DatasetClass.REAL_POPULATED_DATASET,MigrationEligibility.READY_FOR_MIGRATION_PLANNING,"governed",False,"ACTIVE")
    empty=SourceDatasetManifestEntry("CAT-2","x","b.csv",0,DatasetClass.REAL_EMPTY_GOVERNED_REGISTER,MigrationEligibility.DEFERRED_SPATIAL_OR_LEGAL,"governed",True,"ACTIVE")
    assert populated.row_count==2 and empty.row_count==0
    assert empty.relative_path=="x/b.csv"


def test_source_artifact_verifies_bytes_and_hash(tmp_path: Path):
    p=tmp_path/"source.csv"; p.write_bytes(b"a,b\n1,2\n")
    data=p.read_bytes()
    ev=SourceArtifactEvidence("HASH-1","source.csv",sha256(data).hexdigest(),len(data),__import__('datetime').date(2026,8,13))
    assert ev.verify(p)
    p.write_bytes(b"changed")
    assert not ev.verify(p)


def test_source_record_reference_requires_dataset_namespace_and_positive_row():
    ref=SourceRecordReference("dataset:novegeo:test","1","SRC-1","file.csv",7)
    assert ref.row_number==7
    try: SourceRecordReference("bad","1","x","f",1)
    except ValueError: pass
    else: raise AssertionError("invalid dataset id accepted")
