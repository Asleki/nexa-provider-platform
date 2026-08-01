"""Name Authority application permission policy."""
READ="name_authority.read"; SEARCH="name_authority.search"; STATS="name_authority.statistics.read"; MANUAL_CREATE="name_authority.manual_candidate.create"; MANUAL_APPROVE="name_authority.manual_candidate.approve"; COMPOSE="name_authority.composition.create"; SNAPSHOT_READ="name_authority.snapshot.read"; CHANGES_READ="name_authority.changes.read"; SYNC_ACK="name_authority.sync.acknowledge"

class NameAuthorityAuthorization:
    def require(self,context,permission):
        if not context.principal.authenticated: raise PermissionError("authentication required")
        if context.authority_runtime not in context.principal.allowed_runtimes: raise PermissionError("runtime access denied")
        if permission not in context.principal.permissions: raise PermissionError("permission denied")
