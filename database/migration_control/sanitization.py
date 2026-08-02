"""Central secret-safe text sanitization for migration control."""
from __future__ import annotations
import re

_PATTERNS = (
    re.compile(r"(?i)(password\s*=\s*)[^\s;]+"),
    re.compile(r"(?i)(postgres(?:ql)?://)([^\s/@:]+):([^\s/@]+)@"),
    re.compile(r"(?i)(user\s*=\s*)[^\s;]+"),
)

def sanitize_text(value: object, *, limit: int = 500) -> str:
    text = str(value)
    for pattern in _PATTERNS:
        if pattern.pattern.startswith('(?i)(postgres'):
            text = pattern.sub(r"\1[redacted]@", text)
        else:
            text = pattern.sub(r"\1[redacted]", text)
    return text[:limit]
