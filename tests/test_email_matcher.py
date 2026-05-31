import pytest

from cove.email.matcher import JobMatcher, _extract_domain, _extract_token, _normalize_domain, _parse_bare_addr
from cove.email.models import ConfirmationEmail, ConfirmationRequest

_TOKEN = "abc12345"
_BROKER_DOMAIN = "spokeo.com"

_REQUEST = ConfirmationRequest(
    job_token=_TOKEN,
    broker_slug="spokeo",
    broker_domain=_BROKER_DOMAIN,
    sub_address=f"cove+{_TOKEN}@cove.test",
    created_at="2026-01-01T00:00:00Z",
)

_PENDING = {_TOKEN: _REQUEST}


def _make_email(to: str, from_: str, body: str = "") -> ConfirmationEmail:
    return ConfirmationEmail(
        message_id="<test-msg-id@mail.test>",
        to_address=to,
        from_address=from_,
        subject="Please confirm your opt-out request",
        body_text=body,
        received_at="2026-01-01T00:01:00Z",
    )


def test_match_success():
    matcher = JobMatcher(_PENDING)
    email = _make_email(
        to=f"cove+{_TOKEN}@cove.test",
        from_="noreply@spokeo.com",
        body="Click here: https://spokeo.com/confirm/abc",
    )
    result = matcher.match(email)
    assert result.matched is True
    assert result.broker_slug == "spokeo"
    assert result.job_token == _TOKEN
    assert result.confirmation_link.startswith("https://")


def test_match_unknown_token():
    matcher = JobMatcher(_PENDING)
    email = _make_email(to="cove+unknown99@cove.test", from_="noreply@spokeo.com")
    result = matcher.match(email)
    assert result.matched is False
    assert result.reason == "unknown_token"


def test_match_domain_mismatch():
    matcher = JobMatcher(_PENDING)
    email = _make_email(to=f"cove+{_TOKEN}@cove.test", from_="noreply@evil.com")
    result = matcher.match(email)
    assert result.matched is False
    assert result.reason == "domain_mismatch"


def test_match_no_token_in_to():
    matcher = JobMatcher(_PENDING)
    email = _make_email(to="cove@cove.test", from_="noreply@spokeo.com")
    result = matcher.match(email)
    assert result.matched is False
    assert result.reason == "unknown_token"


def test_match_www_broker_domain_accepted():
    """www-prefixed official_url: From noreply@spokeo.com should match spokeo.com."""
    www_request = ConfirmationRequest(
        job_token=_TOKEN,
        broker_slug="spokeo",
        broker_domain="www.spokeo.com",
        sub_address=f"cove+{_TOKEN}@cove.test",
        created_at="2026-01-01T00:00:00Z",
    )
    matcher = JobMatcher({_TOKEN: www_request})
    email = _make_email(to=f"cove+{_TOKEN}@cove.test", from_="noreply@spokeo.com")
    result = matcher.match(email)
    assert result.matched is True


def test_match_subdomain_of_broker_accepted():
    """mail.spokeo.com is an immediate subdomain of spokeo.com — accepted."""
    matcher = JobMatcher(_PENDING)
    email = _make_email(to=f"cove+{_TOKEN}@cove.test", from_="noreply@mail.spokeo.com")
    result = matcher.match(email)
    assert result.matched is True


def test_match_deep_subdomain_rejected():
    """deep.mail.spokeo.com is two levels deep — must be rejected."""
    matcher = JobMatcher(_PENDING)
    email = _make_email(to=f"cove+{_TOKEN}@cove.test", from_="evil@deep.mail.spokeo.com")
    result = matcher.match(email)
    assert result.matched is False
    assert result.reason == "domain_mismatch"


def test_extract_token_valid():
    assert _extract_token("cove+abc12345@cove.test") == "abc12345"


def test_extract_token_no_plus():
    assert _extract_token("cove@cove.test") is None


def test_extract_token_wrong_prefix():
    assert _extract_token("other+abc12345@cove.test") is None


def test_extract_token_empty_token():
    assert _extract_token("cove+@cove.test") is None


def test_extract_domain():
    assert _extract_domain("noreply@spokeo.com") == "spokeo.com"
    assert _extract_domain("no-at-sign") == ""


def test_normalize_domain():
    assert _normalize_domain("www.spokeo.com") == "spokeo.com"
    assert _normalize_domain("spokeo.com") == "spokeo.com"


def test_extract_token_formatted_header():
    """Handles 'Display Name <addr>' format in To header."""
    assert _extract_token("Cove <cove+abc12345@cove.test>") == "abc12345"


def test_extract_domain_formatted_header():
    """Handles 'Display Name <addr>' format in From header."""
    assert _extract_domain("Spokeo <noreply@spokeo.com>") == "spokeo.com"


def test_match_formatted_headers():
    """Full match flow with formatted To and From headers."""
    matcher = JobMatcher(_PENDING)
    email = _make_email(
        to=f"Cove <cove+{_TOKEN}@cove.test>",
        from_="Spokeo <noreply@spokeo.com>",
        body="Click https://spokeo.com/confirm/abc",
    )
    result = matcher.match(email)
    assert result.matched is True
