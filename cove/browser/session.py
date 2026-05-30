"""
BrowserSession: a Playwright context manager with safety constraints.

Safety rules (enforced in code):
- navigate() requires http/https scheme and checks hostname against allowed_hosts
- check_for_captcha() raises CaptchaDetectedError if a CAPTCHA widget is present
- Screenshots use timestamp filenames only (no PII in paths)

Safety rules (by convention — enforced in code review):
- Never pass user-supplied or registry-supplied strings to page.evaluate()
- Never log page content or form field values
- TODO: before the first real scripted adapter merges, add a lint/AST rule
  to prevent page.evaluate() with dynamic strings (ISS or follow-up ticket)
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from cove.browser.captcha import detect_captcha
from cove.browser.errors import BrowserError, CaptchaDetectedError, NavigationBlockedError
from cove.browser.screenshot import save_screenshot

_ALLOWED_SCHEMES = frozenset({"http", "https"})


class BrowserSession:
    """Context manager wrapping a Playwright browser page with safety constraints."""

    def __init__(
        self,
        allowed_hosts: frozenset[str],
        headless: bool = True,
        timeout_ms: int = 30_000,
        screenshot_dir: Path | None = None,
    ) -> None:
        self._allowed_hosts = allowed_hosts
        self._headless = headless
        self._timeout_ms = timeout_ms
        self._screenshot_dir = screenshot_dir
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self) -> BrowserSession:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserError(
                "playwright is not installed; run: "
                "pip install playwright && playwright install chromium"
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        context = self._browser.new_context()
        self._page = context.new_page()
        self._page.set_default_timeout(self._timeout_ms)
        return self

    def __exit__(self, *_) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()

    def navigate(self, url: str) -> None:
        """Navigate to url. Raises NavigationBlockedError if scheme is not http/https
        or if the hostname is not in the registry allowlist."""
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise NavigationBlockedError(
                f"Navigation blocked: scheme {parsed.scheme!r} is not allowed (http/https only)"
            )
        host = parsed.hostname
        if host not in self._allowed_hosts:
            raise NavigationBlockedError(
                f"Navigation to {host!r} blocked — not in registry allowlist"
            )
        self._page.goto(url)

    def check_for_captcha(self) -> None:
        """Raise CaptchaDetectedError if a CAPTCHA element is detected. Call after navigate()."""
        if detect_captcha(self._page):
            raise CaptchaDetectedError("CAPTCHA detected — marking as manual_required")

    @property
    def page(self):
        return self._page

    def save_error_screenshot(self, label: str = "error") -> Path | None:
        """Save an error screenshot if screenshot_dir is configured."""
        if self._screenshot_dir and self._page:
            return save_screenshot(self._page, self._screenshot_dir, label)
        return None
