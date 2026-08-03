"""Repositories for orthography profiles and semantic context relationships."""
class MemoryNameContextRepository:
    def __init__(self): self.profiles={}; self.relationships={}
    def add_profile(self,p):
        existing=self.get_profile_by_name(p.name_id)
        if existing:
            if existing!=p and (existing.structure_type!=p.structure_type or existing.canonical_value_snapshot!=p.canonical_value_snapshot): raise ValueError("orthography profile conflicts with existing profile.")
            return existing
        self.profiles[p.profile_id]=p; return p
    def get_profile_by_name(self,name_id):
        return next((p for p in self.profiles.values() if p.name_id==name_id),None)
    def add_relationship(self,r):
        for x in self.relationships.values():
            if (x.name_id,x.role,x.target_reference_id,x.state)==(r.name_id,r.role,r.target_reference_id,r.state): return x
        self.relationships[r.relationship_id]=r; return r
    def list_relationships(self,name_id): return tuple(x for x in self.relationships.values() if x.name_id==name_id)
__all__=["MemoryNameContextRepository"]
