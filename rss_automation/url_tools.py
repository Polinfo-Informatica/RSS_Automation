"""URL display helpers."""

from __future__ import annotations

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


def redact_url(value: str) -> str:
    """Redact common secret query parameters before logging a URL."""

    parts = urlsplit(value)
    if not parts.query:
        return value

    query = []
    changed = False
    for key, parameter_value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            query.append((key, "REDACTED"))
            changed = True
        else:
            query.append((key, parameter_value))

    if not changed:
        return value

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))
