class BrowserError(Exception):
    """Base class for browser automation errors."""


class NavigationBlockedError(BrowserError):
    """Raised when navigation to a disallowed scheme or host is attempted."""


class CaptchaDetectedError(BrowserError):
    """Raised when CAPTCHA or bot-detection is detected on the current page."""
