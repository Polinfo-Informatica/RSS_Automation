"""URL display helpers."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "apikey",
        "api_key",
        "auth",
        "key",
        "password",
        "secret",
        "token",
    }
)

SENSITIVE_QUERY_PATTERN = re.compile(
    r"(?i)([?&](?:access_token|apikey|api_key|auth|key|password|secret|token)=)([^&\s)>'\"]+)"
)


def redact_text(value: str) -> str:
    """Redact common secret query parameters inside arbitrary text."""

    return SENSITIVE_QUERY_PATTERN.sub(r"\1REDACTED", value)


def redact_url(value: str) -> str:
    """Redact common secret query parameters before logging a URL."""

    parts = urlsplit(value)
    if not parts.query:
        return redact_text(value)

    query = []
    changed = False
    for key, parameter_value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            query.append((key, "REDACTED"))
            changed = True
        else:
            query.append((key, parameter_value))

    if not changed:
        return redact_text(value)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))
