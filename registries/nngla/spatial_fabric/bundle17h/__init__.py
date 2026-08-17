"""P006.7.11.7.11-.12 Bundle 17H smart addressing and house/site bridge."""
from .contracts import *
from .address_policy import allocation_policy_rows, allocation_policies, address_format_rule_rows
from .road_segments import derive_road_segment_candidates, road_segment_rows
from .frontages import form_frontage_candidate
from .address_allocator import normalize_address_number, AddressNumberCollisionError, MemoryAddressAllocator
from .site_bridge import (
    form_site_candidate, form_structure_site_reference, form_site_address_assignment_candidate,
    load_house_crosswalk, load_house_site_requirements, site_meets_house_requirement,
)
from .lifecycle import site_lifecycle_rows, structure_reference_type_rows, advance_site_stage
from .postgresql_contract import load_schema17h_sql, qualify_schema17h_sql
from .qualification import bundle17h_findings, bundle17h_is_qualified

__all__ = [name for name in globals() if not name.startswith("_")]
