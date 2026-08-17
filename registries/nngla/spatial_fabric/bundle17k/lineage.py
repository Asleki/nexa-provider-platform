from __future__ import annotations
from datetime import date
from registries.nngla.parcel_lineage import ParcelLineageRecord
from ._shared import stable_id

def form_subdivision(predecessor,successors,*,effective_on:date,source_reference):
 return ParcelLineageRecord(stable_id('parcel-lineage:',predecessor,*successors,effective_on.isoformat()),'SUBDIVISION',(predecessor,),tuple(successors),effective_on,source_reference)
def form_consolidation(predecessors,successor,*,effective_on:date,source_reference):
 return ParcelLineageRecord(stable_id('parcel-lineage:',*predecessors,successor,effective_on.isoformat()),'CONSOLIDATION',tuple(predecessors),(successor,),effective_on,source_reference)
__all__=['form_subdivision','form_consolidation']
