import logging
import re
import sys

_EMAIL_RE = re.compile(r"[\w.+-]+@(?:[\w-]+\.)+[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}")


class PiiRedactionFilter(logging.Filter):
    """Scrubs emails and phone numbers from log messages before emit."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        msg = _EMAIL_RE.sub("[email]", msg)
        msg = _PHONE_RE.sub("[phone]", msg)
        record.msg = msg
        record.args = ()
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with PII redaction, output to stderr only."""
    logging.basicConfig(
        stream=sys.stderr,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    pii_filter = PiiRedactionFilter()
    for handler in logging.root.handlers:
        if not any(isinstance(f, PiiRedactionFilter) for f in handler.filters):
            handler.addFilter(pii_filter)
