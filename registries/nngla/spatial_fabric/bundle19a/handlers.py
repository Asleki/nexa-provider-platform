"""Bundle 19A domain handlers for pre-existing Bundle 17N runtime commands."""
from __future__ import annotations

from registries.nngla.spatial_fabric.bundle17n.contracts import RuntimeCommand
from registries.nngla.spatial_fabric.bundle17n.dispatcher import RuntimeCommandDispatcher


def make_geometry_association_handler(repository):
    """Return the EXISTING_GEOMETRY_ONLY handler for ASSOCIATE_GEOMETRY.

    This adapter deliberately allocates no geometry identity.  Bundle 17N authorization,
    approval and validation remain authoritative; Bundle 19A only provides domain execution.
    """
    def handler(command: RuntimeCommand):
        if command.command_code != "ASSOCIATE_GEOMETRY":
            raise ValueError("Bundle 19A geometry association handler accepts ASSOCIATE_GEOMETRY only")
        place_id = str(command.payload.get("subject_id", "")).strip()
        geometry_id = str(command.payload.get("geometry_id", "")).strip()
        if not place_id.startswith("NG-PLC-") or not geometry_id.startswith("NG-GEO-"):
            raise ValueError("ASSOCIATE_GEOMETRY requires canonical NG-PLC subject and existing NG-GEO identity")
        references = repository.associate_existing_geometry(place_id=place_id, geometry_id=geometry_id)
        return {"references": references}
    return handler


def register_bundle19a_runtime_handlers(dispatcher: RuntimeCommandDispatcher, repository) -> RuntimeCommandDispatcher:
    dispatcher.register_handler("geometry.associate", make_geometry_association_handler(repository))
    return dispatcher


__all__ = ["make_geometry_association_handler", "register_bundle19a_runtime_handlers"]
