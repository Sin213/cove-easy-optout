import logging

import pytest

from adapters.mock import MockAdapter
from cove.adapter import OptOutStatus
from cove.engine import run_optout
from cove.profile.models import Address, Profile

_PROFILE = Profile(
    names=["Test User"],
    emails=["test@example.com"],
    phones=["555-867-5309"],
    addresses=[Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")],
)


def test_run_optout_mixed_outcomes():
    adapters = [
        MockAdapter(OptOutStatus.submitted),
        MockAdapter(OptOutStatus.manual_required),
        MockAdapter(OptOutStatus.failed),
    ]
    results = run_optout(_PROFILE, adapters)
    assert len(results) == 3
    assert results[0].status == OptOutStatus.submitted
    assert results[1].status == OptOutStatus.manual_required
    assert results[2].status == OptOutStatus.failed


class _ExplodingAdapter(MockAdapter):
    broker_slug = "exploding"
    manual_url = "https://example.com/manual"

    def submit_optout(self, profile):
        raise RuntimeError("network error with secret data in message")


def test_exception_becomes_failed_result():
    results = run_optout(_PROFILE, [_ExplodingAdapter()])
    assert len(results) == 1
    assert results[0].status == OptOutStatus.failed
    assert "RuntimeError" in results[0].message


def test_exception_type_logged_not_message(caplog):
    with caplog.at_level(logging.WARNING):
        run_optout(_PROFILE, [_ExplodingAdapter()])
    log_text = " ".join(r.message for r in caplog.records)
    assert "RuntimeError" in log_text
    # Exception message must NOT appear in logs (may contain PII from HTTP responses)
    assert "secret data in message" not in log_text


def test_no_pii_in_logs(caplog):
    adapters = [MockAdapter(OptOutStatus.submitted)]
    with caplog.at_level(logging.DEBUG):
        run_optout(_PROFILE, adapters)
    for record in caplog.records:
        assert "Test User" not in record.message
        assert "test@example.com" not in record.message
        assert "555-867-5309" not in record.message
