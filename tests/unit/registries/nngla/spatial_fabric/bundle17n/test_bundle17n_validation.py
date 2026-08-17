from registries.nngla.spatial_fabric.bundle17n.contracts import RuntimeCommand
from registries.nngla.spatial_fabric.bundle17n.validation import validate_command
def test_data_driven_validation_fails_closed():
    good=RuntimeCommand("SUBDIVIDE_PARCEL",1,"production","RUNTIME_SCOPED","p","i","c",{"parent_parcel_id":"NG-PAR-1","child_count":2})
    bad=RuntimeCommand("SUBDIVIDE_PARCEL",1,"production","RUNTIME_SCOPED","p","i2","c",{"parent_parcel_id":"","child_count":0})
    assert validate_command(good)==()
    assert {x.field_name for x in validate_command(bad)}=={"parent_parcel_id","child_count"}
