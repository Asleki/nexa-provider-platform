"""Errors for sex-usage metadata enrichment."""
class NameSexUsageError(ValueError): pass
class NameSexUsageMetadataError(NameSexUsageError): pass
__all__=["NameSexUsageError","NameSexUsageMetadataError"]
