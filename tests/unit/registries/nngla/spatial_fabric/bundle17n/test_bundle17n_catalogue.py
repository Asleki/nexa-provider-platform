from registries.nngla.spatial_fabric.bundle17n.command_catalogue import command_definitions,get_command_definition
def test_catalogue_has_known_operational_commands():
    codes={x.command_code for x in command_definitions()}
    assert {"ALLOCATE_ADDRESS","ISSUE_TITLE","SUPERSEDE_GEOMETRY","RESERVE_NAME"} <= codes
    assert get_command_definition("ALLOCATE_ADDRESS").target_family=="ADDRESS_REFERENCE"
