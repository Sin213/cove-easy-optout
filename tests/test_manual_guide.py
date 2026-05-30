import pytest

from adapters._schema.broker import AdapterType, BrokerEntry, Difficulty
from cove.adapter import OptOutStatus
from cove.manual_guide import ManualFlowGenerator
from cove.profile.models import Address, Profile

_BROKER = BrokerEntry(
    slug="mylife",
    name="MyLife",
    adapter_type=AdapterType.manual_only,
    opt_out_url="https://www.mylife.com/privacy/data-opt-out.pubview",
    official_url="https://www.mylife.com",
    difficulty=Difficulty.hard,
    status_language=["manual_required", "profile_not_visible_as_of_date"],
    captcha_expected=True,
    manual_fallback_required=True,
    rescan_days=90,
)

_PROFILE = Profile(
    names=["Test User"],
    emails=["test@example.com"],
    phones=["555-867-5309"],
    addresses=[Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")],
)

_GEN = ManualFlowGenerator()


def test_generate_returns_correct_broker_slug():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert guide.broker_slug == "mylife"
    assert guide.broker_name == "MyLife"


def test_steps_are_numbered_from_one():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert guide.steps[0].number == 1
    assert guide.steps[-1].number == len(guide.steps)


def test_first_step_contains_opt_out_url():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert "mylife.com" in guide.steps[0].instruction


def test_steps_contain_first_name_only():
    guide = _GEN.generate(_BROKER, _PROFILE)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "Test" in all_text
    assert "User" not in all_text  # last name excluded


def test_steps_contain_city_state():
    guide = _GEN.generate(_BROKER, _PROFILE)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "Springfield" in all_text
    assert "IL" in all_text


def test_steps_do_not_contain_email():
    guide = _GEN.generate(_BROKER, _PROFILE)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "test@example.com" not in all_text


def test_steps_do_not_contain_phone():
    guide = _GEN.generate(_BROKER, _PROFILE)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "555-867-5309" not in all_text


def test_rescan_reminder_mentions_rescan_days():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert "90" in guide.rescan_reminder


def test_disclaimer_present():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert "does not guarantee removal" in guide.disclaimer


def test_to_opt_out_result_is_manual_required():
    guide = _GEN.generate(_BROKER, _PROFILE)
    result = guide.to_opt_out_result()
    assert result.status == OptOutStatus.manual_required
    assert result.broker_slug == "mylife"


def test_to_opt_out_result_manual_url_is_str():
    guide = _GEN.generate(_BROKER, _PROFILE)
    result = guide.to_opt_out_result()
    assert isinstance(result.manual_url, str)
    assert result.manual_url.startswith("https://")


def test_empty_names_uses_placeholder():
    profile = Profile(names=[], emails=[], phones=[], addresses=[
        Address(street="1 Main", city="Springfield", state="IL", zip_code="62701")
    ])
    guide = _GEN.generate(_BROKER, profile)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "[Your first name]" in all_text


def test_whitespace_only_name_uses_placeholder():
    profile = Profile(names=["   "], emails=[], phones=[], addresses=[
        Address(street="1 Main", city="Springfield", state="IL", zip_code="62701")
    ])
    guide = _GEN.generate(_BROKER, profile)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "[Your first name]" in all_text


def test_single_token_name_works():
    profile = Profile(names=["Madonna"], emails=[], phones=[], addresses=[
        Address(street="1 Main", city="New York", state="NY", zip_code="10001")
    ])
    guide = _GEN.generate(_BROKER, profile)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "Madonna" in all_text


def test_empty_addresses_uses_placeholder():
    profile = Profile(names=["Test User"], emails=[], phones=[], addresses=[])
    guide = _GEN.generate(_BROKER, profile)
    all_text = " ".join(s.instruction for s in guide.steps)
    assert "[Your city, state]" in all_text


def test_opt_out_url_is_str():
    guide = _GEN.generate(_BROKER, _PROFILE)
    assert isinstance(guide.opt_out_url, str)
