"""P006.7.5 survey and survey-control contracts.

The validated Day-Zero control-point register is intentionally empty; this
module defines the contract without fabricating observations.
"""
from __future__ import annotations
from dataclasses import dataclass
import math, re

@dataclass(frozen=True, slots=True)
class SurveyRecord:
    survey_id: str
    accuracy_class_code: str
    source_reference: str
    instrument_record_reference: str | None
    surveyor_approval_reference: str | None
    status: str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NG-SRV-\d{6}", self.survey_id): raise ValueError("survey_id must use NG-SRV-######")
        if not self.accuracy_class_code or not self.source_reference: raise ValueError("accuracy class and source reference are required")

@dataclass(frozen=True, slots=True)
class SurveyControlPointCandidate:
    survey_control_candidate_id: str
    source_point_id: str
    candidate_role: str
    longitude: float
    latitude: float
    crs_code: str
    accuracy_class_code: str
    qualification_status: str
    source_basis: str
    def __post_init__(self) -> None:
        if not self.survey_control_candidate_id or not self.source_point_id: raise ValueError("survey control candidate/source identity required")
        if not math.isfinite(self.longitude) or not -180 <= self.longitude <= 180: raise ValueError("longitude out of range")
        if not math.isfinite(self.latitude) or not -90 <= self.latitude <= 90: raise ValueError("latitude out of range")
        if self.crs_code != "NG-CRS-EPSG4326": raise ValueError("survey control must declare governed CRS")

class MemorySurveyRepository:
    def __init__(self): self._items: dict[str,SurveyRecord]={}
    def add(self, record: SurveyRecord):
        p=self._items.get(record.survey_id)
        if p is not None and p != record: raise ValueError("survey identifier collision")
        self._items[record.survey_id]=record; return record
    def get(self,survey_id): return self._items.get(survey_id)
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=["SurveyRecord","SurveyControlPointCandidate","MemorySurveyRepository"]
