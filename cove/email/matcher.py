"""
Email-to-job matcher using plus-addressing correlation.

Three invariants must ALL hold to accept a confirmation email:
1. To/Delivered-To contains a recognised job_token (cove+TOKEN@domain.com format)
2. From domain matches broker's registry domain (exact or immediate subdomain)
3. job_token is registered in the pending jobs dict (not spoofed)

DKIM/SPF: From-domain check alone is insufficient against forged From headers.
TODO: verify DKIM/SPF before production use.
"""
from __future__ import annotations

from email.utils import parseaddr

from cove.email.extractor import extract_confirmation_link
from cove.email.models import ConfirmationEmail, ConfirmationRequest, ConfirmationResult


class JobMatcher:
    def __init__(self, pending: dict[str, ConfirmationRequest]) -> None:
        self._pending = pending  # {job_token: ConfirmationRequest}

    def match(self, email: ConfirmationEmail) -> ConfirmationResult:
        token = _extract_token(email.to_address)
        if not token or token not in self._pending:
            return ConfirmationResult(
                job_token=token or "",
                broker_slug="",
                matched=False,
                reason="unknown_token",
                confirmation_link="",
            )
        req = self._pending[token]
        from_domain = _extract_domain(email.from_address)
        base_domain = _normalize_domain(req.broker_domain)

        # Domain comparison: accept exact base match OR exactly one subdomain level deep.
        # e.g. base=spokeo.com accepts: spokeo.com, mail.spokeo.com
        # but NOT: evil.com, evil-spokeo.com, deep.mail.spokeo.com
        # TODO: verify DKIM/SPF before production — From-domain alone can be forged.
        base_parts = base_domain.split(".")
        from_parts = from_domain.split(".")
        _is_immediate_subdomain = (
            len(from_parts) == len(base_parts) + 1
            and from_parts[-len(base_parts):] == base_parts
        )
        if from_domain != base_domain and not _is_immediate_subdomain:
            return ConfirmationResult(
                job_token=token,
                broker_slug=req.broker_slug,
                matched=False,
                reason="domain_mismatch",
                confirmation_link="",
            )

        link = extract_confirmation_link(email.body_text)
        return ConfirmationResult(
            job_token=token,
            broker_slug=req.broker_slug,
            matched=True,
            reason="matched",
            confirmation_link=link,
        )


def _parse_bare_addr(raw: str) -> str:
    """Extract the bare email address from a possibly formatted header value.

    Handles 'Display Name <addr@host>' and plain 'addr@host' forms.
    """
    _, addr = parseaddr(raw)
    return addr


def _extract_token(address: str) -> str | None:
    """Extract job_token from cove plus-address: cove+TOKEN@domain.com -> TOKEN.

    Handles formatted headers like 'Cove <cove+TOKEN@domain.com>'.
    Returns None if:
    - No '@' or '+' in parsed address
    - Local part before '+' is not exactly 'cove' (wrong-prefix bypass guard)
    - Token is empty string (cove+@domain.com)
    """
    addr = _parse_bare_addr(address)
    if "@" not in addr or "+" not in addr:
        return None
    local = addr.split("@")[0]
    parts = local.split("+", 1)
    if len(parts) != 2:
        return None
    prefix, token = parts
    if prefix != "cove":
        return None
    if not token:
        return None
    return token


def _extract_domain(address: str) -> str:
    """Extract domain from email address, lowercase.

    Handles formatted headers like 'Spokeo <noreply@spokeo.com>'.
    """
    addr = _parse_bare_addr(address)
    if "@" not in addr:
        return ""
    return addr.split("@")[-1].lower().strip()


def _normalize_domain(domain: str) -> str:
    """Strip leading 'www.' from domain for broker comparison."""
    return domain.removeprefix("www.")
