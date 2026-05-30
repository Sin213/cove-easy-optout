from unittest.mock import MagicMock, patch, call

import pytest

from cove.browser import allowed_hosts_from_registry
from cove.browser.errors import CaptchaDetectedError, NavigationBlockedError
from cove.browser.session import BrowserSession

_ALLOWED = frozenset({"example.com", "broker.example.org"})


def _make_session(**kwargs) -> BrowserSession:
    return BrowserSession(allowed_hosts=_ALLOWED, **kwargs)



def test_navigate_allowed_host():
    mock_page = MagicMock()
    session = _make_session()
    session._page = mock_page
    session.navigate("https://example.com/optout")
    mock_page.goto.assert_called_once_with("https://example.com/optout")


def test_navigate_blocked_host_raises():
    session = _make_session()
    session._page = MagicMock()
    with pytest.raises(NavigationBlockedError, match="not in registry allowlist"):
        session.navigate("https://notinregistry.com/page")


def test_navigate_javascript_scheme_raises():
    session = _make_session()
    session._page = MagicMock()
    with pytest.raises(NavigationBlockedError, match="not allowed"):
        session.navigate("javascript:alert(1)")


def test_navigate_data_scheme_raises():
    session = _make_session()
    session._page = MagicMock()
    with pytest.raises(NavigationBlockedError, match="not allowed"):
        session.navigate("data:text/html,<script>x</script>")


def test_navigate_file_scheme_raises():
    session = _make_session()
    session._page = MagicMock()
    with pytest.raises(NavigationBlockedError, match="not allowed"):
        session.navigate("file:///etc/passwd")


def test_check_for_captcha_raises_when_detected():
    session = _make_session()
    mock_page = MagicMock()
    session._page = mock_page
    with patch("cove.browser.session.detect_captcha", return_value=True):
        with pytest.raises(CaptchaDetectedError):
            session.check_for_captcha()


def test_check_for_captcha_no_raise_when_clean():
    session = _make_session()
    session._page = MagicMock()
    with patch("cove.browser.session.detect_captcha", return_value=False):
        session.check_for_captcha()  # should not raise


def test_browser_closed_on_exit():
    mock_browser = MagicMock()
    mock_pw = MagicMock()
    session = _make_session()
    session._browser = mock_browser
    session._playwright = mock_pw
    session.__exit__(None, None, None)
    mock_browser.close.assert_called_once()
    mock_pw.stop.assert_called_once()


def test_playwright_stopped_even_if_browser_close_raises():
    """playwright.stop() must be called even if browser.close() raises."""
    mock_browser = MagicMock()
    mock_browser.close.side_effect = RuntimeError("teardown error")
    mock_pw = MagicMock()
    session = _make_session()
    session._browser = mock_browser
    session._playwright = mock_pw
    with pytest.raises(RuntimeError):
        session.__exit__(None, None, None)
    mock_pw.stop.assert_called_once()


def test_allowed_hosts_from_registry():
    from adapters._schema.broker import AdapterType, BrokerEntry, Difficulty
    entry = BrokerEntry(
        slug="test-broker",
        name="Test Broker",
        adapter_type=AdapterType.scripted,
        opt_out_url="https://optout.test-broker.com/remove",
        official_url="https://www.test-broker.com",
        difficulty=Difficulty.easy,
        status_language=["submitted", "manual_required"],
    )
    hosts = allowed_hosts_from_registry({"test-broker": entry})
    assert "optout.test-broker.com" in hosts
    assert "www.test-broker.com" in hosts
    assert len(hosts) == 2
