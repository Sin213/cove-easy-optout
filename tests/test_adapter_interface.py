import logging

import pytest

from adapters.mock import MockAdapter
from cove.adapter import OptOutStatus
from cove.profile.models import Address, Profile

_PROFILE = Profile(
    names=["Test User"],
    emails=["test@example.com"],
    phones=["555-867-5309"],
    addresses=[Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")],
)


def test_default_outcome_is_submitted():
    adapter = MockAdapter()
    result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.submitted
    assert result.broker_slug == "mock"


def test_manual_required_outcome():
    adapter = MockAdapter(OptOutStatus.manual_required)
    result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url  # non-empty


def test_manual_url_is_static_not_profile_derived():
    adapter = MockAdapter(OptOutStatus.manual_required)
    result = adapter.submit_optout(_PROFILE)
    assert "test@example.com" not in result.manual_url
    assert "Test User" not in result.manual_url


def test_failed_outcome():
    adapter = MockAdapter(OptOutStatus.failed)
    result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.failed
    assert result.message  # non-empty


def test_awaiting_confirmation_outcome():
    adapter = MockAdapter(OptOutStatus.awaiting_confirmation)
    result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.awaiting_confirmation


def test_profile_not_visible_outcome():
    adapter = MockAdapter(OptOutStatus.profile_not_visible_as_of_date)
    result = adapter.submit_optout(_PROFILE)
    assert result.status == OptOutStatus.profile_not_visible_as_of_date


def test_verify_removal_default_returns_manual_required():
    adapter = MockAdapter()
    result = adapter.verify_removal(_PROFILE)
    assert result.status == OptOutStatus.manual_required
    assert result.manual_url == MockAdapter.manual_url


def test_submit_optout_no_pii_in_logs(caplog):
    adapter = MockAdapter()
    with caplog.at_level(logging.DEBUG):
        adapter.submit_optout(_PROFILE)
    for record in caplog.records:
        assert "Test User" not in record.message
        assert "test@example.com" not in record.message
        assert "555-867-5309" not in record.message
