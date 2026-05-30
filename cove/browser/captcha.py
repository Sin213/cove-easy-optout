"""
CAPTCHA detection via DOM element selectors.

Limitation: invisible CAPTCHAs (reCAPTCHA v3, Cloudflare JS challenge, some
Arkose Labs deployments) produce no detectable DOM element. Brokers known to
use invisible CAPTCHA must set captcha_expected=True + manual_fallback_required=True
in the registry — the adapter will return manual_required without attempting detection.
"""
from __future__ import annotations

# Selectors for detectable CAPTCHA widgets. Extend as new patterns are discovered.
_CAPTCHA_SELECTORS = [
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    "iframe[src*='turnstile']",
    "[class*='captcha']",
    "[id*='captcha']",
]


def detect_captcha(page) -> bool:
    """Return True if a CAPTCHA element is detected on the page.

    Only catches playwright.sync_api.Error (element-lookup failures).
    All other exceptions propagate — a page crash or network error must not
    silently allow automation to continue.
    """
    from playwright.sync_api import Error as PlaywrightError

    for selector in _CAPTCHA_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except PlaywrightError:
            # Element lookup error — treat as not found, check next selector
            pass
        # Any other exception (page crash, RuntimeError, etc.) propagates
    return False
