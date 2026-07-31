"""Deterministic, repository-neutral CSV reader for name candidates."""
from __future__ import annotations
import csv, io
from .name_csv_errors import NameCsvHeaderError,NameCsvRowError
from .name_csv_row import NameCsvRow
_REQUIRED=("name","name_kind")
class NameCsvReader:
    def __init__(self,*,allow_unknown_columns:bool=False)->None: self._allow_unknown=bool(allow_unknown_columns)
    def read_text(self,text:str)->tuple[NameCsvRow,...]:
        if not isinstance(text,str): raise TypeError("text must be text.")
        stream=io.StringIO(text,newline="")
        reader=csv.DictReader(stream)
        if reader.fieldnames is None: raise NameCsvHeaderError("CSV header is required.")
        fields=[]
        for raw in reader.fieldnames:
            if raw is None: raise NameCsvHeaderError("CSV header names cannot be empty.")
            key=raw.strip().lower()
            if not key: raise NameCsvHeaderError("CSV header names cannot be empty.")
            if key in fields: raise NameCsvHeaderError(f"duplicate CSV header: {key}.")
            fields.append(key)
        missing=[name for name in _REQUIRED if name not in fields]
        if missing: raise NameCsvHeaderError(f"missing required CSV header(s): {', '.join(missing)}.")
        allowed={"name","name_kind","sex_usage","source_reference","external_record_id","language_refs","country_refs","region_refs","culture_refs","script_code","runtime_mode"}
        unknown=[name for name in fields if name not in allowed]
        if unknown and not self._allow_unknown: raise NameCsvHeaderError(f"unknown CSV header(s): {', '.join(unknown)}.")
        rows=[]
        for row_number,row in enumerate(reader,start=2):
            if None in row: raise NameCsvRowError(f"row {row_number} has more values than headers.")
            values={fields[i]:(row.get(reader.fieldnames[i]) or "") for i in range(len(fields))}
            if not any(v.strip() for v in values.values()): continue
            rows.append(NameCsvRow(row_number,values))
        return tuple(rows)
__all__=["NameCsvReader"]
