"""Read-only Bundle 14A migration/source snapshot loader.

These CSV files are governed source evidence, not canonical runtime storage.
"""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path
from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import RecordEffectScope
from .authority import NNGLAAuthority, NNGLAAuthorityRole, AuthorityRoleCode, AuthorityStatus
from .domain_catalogue import NNGLARecordFamily, DomainRuntimeRule, NNGLADomainCatalogue
from .spatial_identifiers import SpatialNamespace, SpatialIdentifierFormat, SpatialIdentifierCatalogue
from .lifecycle import SpatialLifecycleStatus, SpatialLifecycleDefinition

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "novegeo" / "nngla" / "foundation" / "source"

def _rows(name: str, root: Path = DEFAULT_SOURCE_ROOT):
    with (root / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def _bool(value: str) -> bool:
    if value.lower() not in {"true","false"}: raise ValueError(f"invalid boolean {value!r}")
    return value.lower() == "true"

def _date(value: str): return date.fromisoformat(value) if value else None

def load_authority(root: Path = DEFAULT_SOURCE_ROOT):
    row = _rows("novegeo_authority_record.csv", root)[0]
    authority = NNGLAAuthority(row["authority_id"], row["authority_code"], row["official_name"], row["authority_type"], row["world_realm_id"], row["country_record_id"], row["mandate_summary"], AuthorityStatus(row["status"]), _date(row["effective_from"]), _date(row["effective_to"]), row["source_reference"])
    roles = tuple(NNGLAAuthorityRole(r["authority_role_id"], r["authority_id"], AuthorityRoleCode(r["role_code"]), r["role_name"], r["domain_scope"], *[_bool(r[k]) for k in ("may_create","may_review","may_approve","may_gazette","may_retire")], AuthorityStatus(r["status"]), _date(r["effective_from"]), _date(r["effective_to"])) for r in _rows("novegeo_authority_role_register.csv", root))
    return authority, roles

def load_domain_catalogue(root: Path = DEFAULT_SOURCE_ROOT):
    rules=[]
    for r in _rows("nexilabs_runtime_authority_matrix.csv", root):
        if r["authority_code"] != "NNGLA": continue
        rules.append(DomainRuntimeRule(NNGLARecordFamily(r["record_family"]), OperationRuntimeMode(r["runtime_code"].lower()), r["permission_code"], RecordEffectScope(r["effect_scope_code"]), _bool(r["approval_required"]), r["status"]))
    return NNGLADomainCatalogue(tuple(rules))

def load_identifier_catalogue(root: Path = DEFAULT_SOURCE_ROOT):
    namespaces=tuple(SpatialNamespace(r["namespace_id"],r["namespace_prefix"],r["namespace_name"],r["object_family"],r["issuing_authority_code"],r["format_rule"],r["example_value"],_bool(r["immutable_after_issue"]),_bool(r["reusable_after_retirement"]),r["status"],_date(r["effective_from"])) for r in _rows("novegeo_code_namespace.csv",root))
    formats=[]
    for r in _rows("novegeo_identifier_format_register.csv",root):
        width=None if r["sequence_width"]=="variable" else int(r["sequence_width"])
        formats.append(SpatialIdentifierFormat(r["identifier_format_id"],r["namespace_id"],r["object_family"],r["prefix"],r["regex_pattern"],width,_bool(r["case_sensitive"]),r["check_digit_rule"],r["example_identifier"],_bool(r["immutable"]),_bool(r["runtime_scoped"]),r["issuing_authority_code"],r["status"]))
    return SpatialIdentifierCatalogue(namespaces,tuple(formats))

def load_lifecycle_definitions(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(SpatialLifecycleDefinition(SpatialLifecycleStatus(r["lifecycle_status_code"]),r["canonical_label"],r["applies_to_origin_class"],_bool(r["allows_geometry"]),_bool(r["allows_official_name"]),_bool(r["terminal_status"]),int(r["status_rank"]),r["description"],r["status"]) for r in _rows("feature_lifecycle_status_codes.csv",root))
