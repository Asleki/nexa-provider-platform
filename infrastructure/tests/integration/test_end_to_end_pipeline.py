from infrastructure.ingestion import DatasetIngestionPipeline
from infrastructure.ingestion.csv import CSVSourceReader
from infrastructure.governance.validation import *
from infrastructure.governance.qualification import *
from infrastructure.governance.publication import *
def test_generic_dataset_moves_from_source_to_publication():
    receipt=DatasetIngestionPipeline((CSVSourceReader(),)).ingest(source_package_id="source:pkg",source_file_id="source:file",filename="datasets.csv",media_type="text/csv",data=b"dataset_id,title,runtime_mode,visibility,lifecycle_status\ndataset:demo,Demo,production,public,active\n",ingestion_run_id="ingestion:demo")
    validation=ValidationEngine((RequiredFieldsRule("dataset_id","title","runtime_mode","visibility","lifecycle_status"),NamespacedIdentifierRule("dataset_id"),AllowedValueRule("runtime_mode",{"production","simulation","shared_reference"}),AllowedValueRule("visibility",{"public","internal","restricted","confidential"}))).validate(receipt.candidates,ValidationContext("rules:dataset",1,"production"),"validation:demo")
    qualification=QualificationService().qualify(QualificationRequest("qualification:demo","validation:demo","actor:submitter","actor:approver"),validation)
    assert qualification.decision is QualificationDecision.qualified
    row=receipt.candidates[0].payload
    service=PublicationService(InMemoryPublicationRepository())
    service.publish(PublicationRecord("publication:demo",row["dataset_id"],1,row["title"],row["runtime_mode"],row["visibility"],row["lifecycle_status"],{"message":"approved generic dataset"}))
    assert service.get_public("publication:demo").to_public_dict()["datasetId"]=="dataset:demo"
