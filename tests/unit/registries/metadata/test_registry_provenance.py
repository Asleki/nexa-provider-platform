from datetime import datetime, timezone
import pytest
from registries.metadata import RegistryProvenance, RegistryProvenanceError, RegistryProvenanceSourceType

def test_generated_provenance_records_reproducibility_reference():
    item = RegistryProvenance("simulation_generator", "nexilabs", generated=True, generator_name="population-generator", generator_version="1", generation_batch_id="NVG-1", generation_seed_reference="seed-hash", recorded_at=datetime(2026,1,1,tzinfo=timezone.utc))
    assert item.source_type is RegistryProvenanceSourceType.SIMULATION_GENERATOR
    assert item.to_dict()["generation_batch_id"] == "NVG-1"

def test_generated_provenance_requires_generator_information():
    with pytest.raises(RegistryProvenanceError): RegistryProvenance("simulation_generator", "nexilabs", generated=True)
