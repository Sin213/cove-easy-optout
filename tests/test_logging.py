import logging

from cove.logging_config import PiiRedactionFilter


def _make_logger(name: str) -> tuple[logging.Logger, list[str]]:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    captured: list[str] = []

    class CapturingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(self.format(record))

    handler = CapturingHandler()
    handler.addFilter(PiiRedactionFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger, captured


def test_email_redacted():
    logger, captured = _make_logger("test.email")
    logger.info("Contact user@example.com for details")
    assert captured
    assert "[email]" in captured[0]
    assert "user@example.com" not in captured[0]


def test_phone_redacted():
    logger, captured = _make_logger("test.phone")
    logger.info("Call 555-867-5309 to confirm")
    assert captured
    assert "[phone]" in captured[0]
    assert "555-867-5309" not in captured[0]


def test_subdomain_email_redacted():
    logger, captured = _make_logger("test.subdomain")
    logger.info("Contact user@mail.example.com for details")
    assert captured
    assert "[email]" in captured[0]
    assert "@" not in captured[0]
    assert "user@mail.example.com" not in captured[0]


def test_non_pii_passes_through():
    logger, captured = _make_logger("test.clean")
    logger.info("Processing broker whitepages status=submitted")
    assert captured
    assert "Processing broker whitepages status=submitted" in captured[0]


def test_both_pii_types_in_one_message():
    logger, captured = _make_logger("test.both")
    logger.info("Email user@example.com phone 555-867-5309 submitted")
    assert captured
    assert "[email]" in captured[0]
    assert "[phone]" in captured[0]
    assert "user@example.com" not in captured[0]
    assert "555-867-5309" not in captured[0]
