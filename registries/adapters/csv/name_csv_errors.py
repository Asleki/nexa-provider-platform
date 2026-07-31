"""CSV adapter errors for M009.10 controlled name ingestion."""
class NameCsvError(ValueError): pass
class NameCsvHeaderError(NameCsvError): pass
class NameCsvRowError(NameCsvError): pass
__all__=["NameCsvError","NameCsvHeaderError","NameCsvRowError"]
