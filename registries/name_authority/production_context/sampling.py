"""Reproducible, diverse source-row sampling."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,random
@dataclass(frozen=True,slots=True)
class SamplingResult:
    strategy:str; random_seed:int; selected_rows:tuple; source_record_ids:tuple[str,...]; fingerprint:str; distribution:dict
class DeterministicDiverseSampler:
    def sample(self,rows,size,random_seed=0,stratify_fields=("gender","origin","language")):
        rows=list(rows)
        if size<1 or size>len(rows): raise ValueError("sample size is outside source bounds.")
        rng=random.Random(int(random_seed)); rng.shuffle(rows)
        selected=[]; seen={f:set() for f in stratify_fields}
        for row in rows:
            data=getattr(row,"data",row if isinstance(row,dict) else {})
            novelty=sum(1 for f in stratify_fields if str(data.get(f) or data.get(f.title()) or "").casefold() not in seen[f])
            if novelty or not selected:
                selected.append(row)
                for f in stratify_fields: seen[f].add(str(data.get(f) or data.get(f.title()) or "").casefold())
                if len(selected)==size: break
        for row in rows:
            if len(selected)==size: break
            if row not in selected: selected.append(row)
        ids=tuple(str((getattr(r,"data",r)).get("id") or (getattr(r,"data",r)).get("ID") or getattr(r,"row_number","")) for r in selected)
        material="|".join(ids)+f"|{random_seed}|diverse-v1"; fp=hashlib.sha256(material.encode()).hexdigest()
        dist={f:sorted(x for x in seen[f] if x) for f in stratify_fields}
        return SamplingResult("deterministic_diverse",int(random_seed),tuple(selected),ids,fp,dist)
__all__=["SamplingResult","DeterministicDiverseSampler"]
