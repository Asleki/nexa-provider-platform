from infrastructure.governance.publication import InMemoryPublicationRepository, PublicationService
class PublicationApplicationService(PublicationService):
    pass
def build_default_publication_service(): return PublicationApplicationService(InMemoryPublicationRepository())
