from unittest.mock import MagicMock, patch

import pytest

from cove.browser.captcha import detect_captcha


def _make_page(count_value: int = 0) -> MagicMock:
    page = MagicMock()
    locator = MagicMock()
    locator.count.return_value = count_value
    page.locator.return_value = locator
    return page


def test_no_captcha_returns_false():
    page = _make_page(count_value=0)
    assert detect_captcha(page) is False


def test_captcha_detected_returns_true():
    page = _make_page(count_value=1)
    assert detect_captcha(page) is True


def test_playwright_error_on_selector_returns_false():
    """PlaywrightError on a selector is swallowed — treated as not found."""
    from playwright.sync_api import Error as PlaywrightError
    page = MagicMock()
    locator = MagicMock()
    locator.count.side_effect = PlaywrightError("element not found")
    page.locator.return_value = locator
    assert detect_captcha(page) is False


def test_non_playwright_exception_propagates():
    """Non-Playwright exceptions (page crashes, etc.) must NOT be swallowed."""
    page = MagicMock()
    locator = MagicMock()
    locator.count.side_effect = RuntimeError("page crashed")
    page.locator.return_value = locator
    with pytest.raises(RuntimeError, match="page crashed"):
        detect_captcha(page)
