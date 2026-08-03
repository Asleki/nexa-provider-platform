"""Facade for M009.13.10 schema and production-authoring qualification."""
from __future__ import annotations


class ReferenceRegistryQualificationService:
    def __init__(self, schema_inspector, production_qualifier) -> None:
        self.schema_inspector = schema_inspector
        self.production_qualifier = production_qualifier

    def inspect_schema(self, schemas=("reference", "migration_control")):
        return self.schema_inspector.inspect(tuple(schemas))

    def qualify_production_name(self, request):
        return self.production_qualifier.qualify(request)

    def qualify(self, request, schemas=("reference", "migration_control")):
        return {
            "schema": self.inspect_schema(schemas),
            "production_name": self.qualify_production_name(request),
        }


__all__ = ["ReferenceRegistryQualificationService"]
