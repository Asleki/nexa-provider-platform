from database.reference_qualification.service import ReferenceRegistryQualificationService


class Inspector:
    def inspect(self, schemas):
        return ("schema", schemas)


class Qualifier:
    def qualify(self, request):
        return ("production", request)


def test_facade_keeps_schema_and_authoring_operations_separate():
    service = ReferenceRegistryQualificationService(Inspector(), Qualifier())
    assert service.inspect_schema(("reference",)) == ("schema", ("reference",))
    assert service.qualify_production_name("request") == ("production", "request")
    assert service.qualify("request", ("reference",)) == {
        "schema": ("schema", ("reference",)),
        "production_name": ("production", "request"),
    }
