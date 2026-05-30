from __future__ import annotations

import re

_URL_RE = re.compile(r"https?://[^\s<>\"']+")

_OPT_OUT_KEYWORDS = ("confirm", "verify", "suppress", "remove", "unsubscribe", "optout")


def extract_confirmation_link(body_text: str) -> str:
    """Extract first confirmation-like URL from plain-text email body.

    Prefers URLs containing opt-out keywords. Falls back to first URL found.
    Strips trailing punctuation that email prose appends after URLs.
    Returns "" if no URL found.
    """
    urls = _URL_RE.findall(body_text)
    if not urls:
        return ""
    preferred = [u for u in urls if any(k in u.lower() for k in _OPT_OUT_KEYWORDS)]
    result = preferred[0] if preferred else urls[0]
    return result.rstrip(".,;:!?)")
