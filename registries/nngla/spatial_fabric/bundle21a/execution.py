"""SQL-neutral execution facade: caller supplies live geometry/state and separated actors."""
from .projection import publish

def execute_candidate(candidate, *, geometry_id, geometry_version=1, naming_status=None, geometry_publication_status=None, submitted_by, approved_by):
    return publish(candidate,geometry_id=geometry_id,geometry_version=geometry_version,naming_status=naming_status,geometry_publication_status=geometry_publication_status,submitted_by=submitted_by,approved_by=approved_by)
