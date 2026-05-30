from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pydantic import ValidationError

from adapters._schema.broker import AdapterType, BrokerEntry
from adapters.registry import load_registry
from cove.cli import main

BROKERS_DIR = Path(__file__).parent.parent / "adapters" / "brokers"


def _write_broker(tmp_path: Path, slug: str, overrides: dict) -> Path:
    base = {
        "slug": slug,
        "name": "Test Broker",
        "adapter_type": "scripted",
        "opt_out_url": "https://example.com/optout",
        "official_url": "https://example.com",
        "difficulty": "easy",
        "region": "us",
        "rescan_days": 30,
        "status_language": ["submitted", "manual_required"],
        "requires_dob": False,
        "requires_email_confirm": False,
        "captcha_expected": False,
        "fcra_regulated": False,
        "manual_fallback_required": False,
    }
    base.update(overrides)
    p = tmp_path / f"{slug}.yaml"
    p.write_text(yaml.dump(base))
    return p


def test_valid_broker_loads(tmp_path):
    _write_broker(tmp_path, "test-broker", {})
    entries = load_registry(tmp_path)
    assert "test-broker" in entries
    entry = entries["test-broker"]
    assert entry.adapter_type == AdapterType.scripted
    assert entry.difficulty.value == "easy"


def test_all_sample_brokers_load():
    entries = load_registry(BROKERS_DIR)
    assert "whitepages" in entries
    assert "spokeo" in entries
    assert "intelius" in entries
    assert len(entries) == 3


def test_whitepages_fields():
    entries = load_registry(BROKERS_DIR)
    wp = entries["whitepages"]
    assert wp.adapter_type == AdapterType.scripted
    assert not wp.fcra_regulated
    assert not wp.captcha_expected


def test_intelius_captcha_manual_fallback():
    entries = load_registry(BROKERS_DIR)
    il = entries["intelius"]
    assert il.captcha_expected
    assert il.manual_fallback_required
    assert il.adapter_type == AdapterType.manual_only


def test_invalid_status_value_raises(tmp_path):
    _write_broker(tmp_path, "bad-status", {"status_language": ["removed"]})
    with pytest.raises(ValidationError, match="Unapproved status values"):
        load_registry(tmp_path)


def test_fcra_scripted_raises(tmp_path):
    _write_broker(tmp_path, "fcra-broker", {"fcra_regulated": True, "adapter_type": "scripted"})
    with pytest.raises(ValidationError, match="manual_only"):
        load_registry(tmp_path)


def test_captcha_without_manual_fallback_raises(tmp_path):
    _write_broker(tmp_path, "captcha-broker", {
        "captcha_expected": True,
        "manual_fallback_required": False,
    })
    with pytest.raises(ValidationError, match="manual_fallback_required"):
        load_registry(tmp_path)


def test_invalid_slug_raises(tmp_path):
    _write_broker(tmp_path, "valid-filename", {"slug": "INVALID SLUG"})
    with pytest.raises(ValidationError, match="lowercase alphanumeric"):
        load_registry(tmp_path)


def test_slug_mismatch_raises(tmp_path):
    _write_broker(tmp_path, "filename-slug", {"slug": "different-slug"})
    with pytest.raises(ValueError, match="does not match filename"):
        load_registry(tmp_path)


def test_slug_with_leading_hyphen_raises(tmp_path):
    _write_broker(tmp_path, "valid-name", {"slug": "-leading"})
    with pytest.raises(ValidationError, match="lowercase alphanumeric"):
        load_registry(tmp_path)


def test_rescan_days_zero_raises(tmp_path):
    _write_broker(tmp_path, "zero-rescan", {"rescan_days": 0})
    with pytest.raises(ValidationError):
        load_registry(tmp_path)


def test_empty_status_language_raises(tmp_path):
    _write_broker(tmp_path, "empty-status", {"status_language": []})
    with pytest.raises(ValidationError, match="at least one value"):
        load_registry(tmp_path)


def test_cli_validate_registry_exits_zero():
    result = CliRunner().invoke(main, ["validate-registry"])
    assert result.exit_code == 0
    assert "3 broker(s)" in result.output


def test_cli_validate_registry_invalid_exits_nonzero(tmp_path):
    _write_broker(tmp_path, "bad", {"status_language": ["deleted"]})
    result = CliRunner().invoke(main, ["validate-registry", "--brokers-dir", str(tmp_path)])
    assert result.exit_code != 0
