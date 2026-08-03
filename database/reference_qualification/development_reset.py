"""Development-only, preview-bound catalogue reset."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
TABLES=(
"reference.name_context_relationship","reference.name_orthography_profile","reference.name_generation_result","reference.name_generation_checkpoint","reference.name_generation_batch","reference.name_generation_source_member","reference.name_generation_source_snapshot","reference.name_authority_component","reference.name_authority_record","reference.manual_name_candidate","reference.canonical_name")
@dataclass(frozen=True,slots=True)
class ResetPlan:
    database_name:str; environment:str; counts:dict; plan_checksum:str
class DevelopmentCatalogueReset:
    def __init__(self,factory): self.factory=factory
    def preview(self,database_name,environment):
        self._guard(database_name,environment); c=self.factory()
        try:
            cur=c.cursor(); counts={}
            for t in TABLES:
                try: cur.execute(f"SELECT COUNT(*) FROM {t}"); counts[t]=int(cur.fetchone()[0])
                except Exception: c.rollback(); counts[t]=0
            material=json.dumps({"database":database_name,"environment":environment,"counts":counts},sort_keys=True); return ResetPlan(database_name,environment,counts,hashlib.sha256(material.encode()).hexdigest())
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    def execute(self,plan,confirmation):
        self._guard(plan.database_name,plan.environment)
        expected=f"RESET NAME CATALOGUE {plan.database_name} {plan.plan_checksum[:12]}"
        if confirmation!=expected: raise ValueError("development reset was not confirmed.")
        current=self.preview(plan.database_name,plan.environment)
        if current.plan_checksum!=plan.plan_checksum: raise ValueError("reset plan drifted; preview again.")
        c=self.factory()
        try:
            cur=c.cursor(); cur.execute("SELECT pg_advisory_xact_lock(%s)",(91310,))
            for t in TABLES: cur.execute(f"DELETE FROM {t}")
            c.commit(); return self.preview(plan.database_name,plan.environment)
        except Exception: c.rollback(); raise
        finally:
            close=getattr(c,"close",None)
            if callable(close): close()
    @staticmethod
    def _guard(database_name,environment):
        if environment!="development" or database_name!="npp_dev": raise ValueError("catalogue reset is restricted to development npp_dev.")
