import logging
from unittest.mock import MagicMock, patch, call

import pytest

from adapters.whitepages import WhitepagesAdapter
from cove.adapter import OptOutStatus
from cove.browser.errors import CaptchaDetectedError, NavigationBlockedError
from cove.profile.models import Address, Profile

_ALLOWED = frozenset({"www.whitepages.com"})

_PROFILE = Profile(
    names=["Test User"],
    emails=["test@example.com"],
    phones=["555-867-5309"],
    addresses=[Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")],
)


def _make_adapter() -> WhitepagesAdapter:
    return WhitepagesAdapter(allowed_hosts=_ALLOWED)


def _mock_session(
    captcha_side_effects=None,
    optout_count=1,
    submit_count=1,
):
    """Build a mock BrowserSession context manager.

    captcha_side_effects: list of return values or exceptions for check_for_captcha calls
    optout_count: how many "Remove me" links the mock page reports
    submit_count: how many submit buttons the mock page reports
    """
    page = MagicMock()

    # "Remove me" locator
    optout_locator = MagicMock()
    optout_locator.count.return_value = optout_count
    optout_locator.first = MagicMock()

    # Submit button locator
    submit_locator = MagicMock()
    submit_locator.count.return_value = submit_count
    submit_locator.first = MagicMock()

    page.get_by_text.return_value = optout_locator
    page.get_by_role.return_value = submit_locator

    session = MagicMock()
    session.page = page
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)

    if captcha_side_effects:
        session.check_for_captcha.side_effect = captcha_side_effects

    return session


def test_happy_path_returns_submitted():
    adapter = _make_adapter()
    mock_session = _mock_session()
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.submitted
    assert result.broker_slug == "whitepages"


def test_no_listing_returns_profile_not_visible():
    adapter = _make_adapter()
    mock_session = _mock_session(optout_count=0)
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.profile_not_visible_as_of_date


def test_captcha_on_navigate_returns_manual_required():
    adapter = _make_adapter()
    mock_session = _mock_session(captcha_side_effects=[CaptchaDetectedError("captcha")])
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == WhitepagesAdapter.manual_url


def test_captcha_on_results_page_returns_manual_required():
    adapter = _make_adapter()
    # First check_for_captcha passes, second raises
    mock_session = _mock_session(captcha_side_effects=[None, CaptchaDetectedError("captcha")])
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == WhitepagesAdapter.manual_url


def test_captcha_on_confirmation_page_returns_manual_required():
    adapter = _make_adapter()
    # First two checks pass, third raises (confirmation page)
    mock_session = _mock_session(
        captcha_side_effects=[None, None, CaptchaDetectedError("captcha")]
    )
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == WhitepagesAdapter.manual_url


def test_empty_name_string_returns_failed_no_browser():
    adapter = _make_adapter()
    profile = Profile(names=[""], emails=[], phones=[], addresses=[
        Address(street="123 Main", city="Springfield", state="IL", zip_code="62701")
    ])
    with patch("adapters.whitepages.BrowserSession") as MockSession:
        result = adapter.submit_optout(profile)
    assert result.status == OptOutStatus.failed
    MockSession.assert_not_called()


def test_no_confirmation_button_returns_manual_required():
    adapter = _make_adapter()
    mock_session = _mock_session(submit_count=0)
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == WhitepagesAdapter.manual_url


def test_missing_names_returns_failed_no_browser():
    adapter = _make_adapter()
    profile = Profile(names=[], emails=[], phones=[], addresses=[
        Address(street="123 Main", city="Springfield", state="IL", zip_code="62701")
    ])
    with patch("adapters.whitepages.BrowserSession") as MockSession:
        result = adapter.submit_optout(profile)
    assert result.status == OptOutStatus.failed
    MockSession.assert_not_called()


def test_missing_addresses_returns_failed_no_browser():
    adapter = _make_adapter()
    profile = Profile(names=["Test User"], emails=[], phones=[], addresses=[])
    with patch("adapters.whitepages.BrowserSession") as MockSession:
        result = adapter.submit_optout(profile)
    assert result.status == OptOutStatus.failed
    MockSession.assert_not_called()


def test_navigation_blocked_returns_failed():
    adapter = _make_adapter()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.navigate.side_effect = NavigationBlockedError("blocked")
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.failed
    assert "NavigationBlockedError" in result.message


def test_unexpected_exception_returns_failed():
    adapter = _make_adapter()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.navigate.side_effect = RuntimeError("network timeout")
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.failed
    assert "RuntimeError" in result.message
    assert "network timeout" not in result.message  # exception message must not leak


def test_verify_removal_returns_manual_required():
    adapter = _make_adapter()
    result = adapter.verify_removal(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == WhitepagesAdapter.manual_url


def test_no_pii_in_messages():
    adapter = _make_adapter()
    mock_session = _mock_session()
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        result = adapter.submit_optout(_PROFILE)
    assert "Test User" not in result.message
    assert "test@example.com" not in result.message
    assert "555-867-5309" not in result.message


def test_no_pii_in_logs(caplog):
    adapter = _make_adapter()
    mock_session = _mock_session()
    with patch("adapters.whitepages.BrowserSession", return_value=mock_session):
        with caplog.at_level(logging.DEBUG):
            adapter.submit_optout(_PROFILE)
    for record in caplog.records:
        assert "Test User" not in record.message
        assert "test@example.com" not in record.message
        assert "555-867-5309" not in record.message
