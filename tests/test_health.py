import json
from pathlib import Path

from click.testing import CliRunner

from cove.cli import main
from cove.health import (
    AdapterHealthChecker,
    BrokerStatus,
    SelectorCheck,
    generate_broker_status,
    write_broker_status,
)

_CHECKER = AdapterHealthChecker()


def _write_fixture(tmp_path: Path, slug: str, filename: str, content: str) -> Path:
    d = tmp_path / slug
    d.mkdir(parents=True, exist_ok=True)
    p = d / filename
    p.write_text(content)
    return p


_FIXTURE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <form action="#">
    <input type="text" name="name" />
    <button type="submit">Search</button>
  </form>
  <a class="optout-link">Remove me</a>
</body>
</html>
"""


def test_check_fixture_all_present(tmp_path):
    _write_fixture(tmp_path, "broker", "page.html", _FIXTURE_HTML)
    checks = [
        SelectorCheck("text", "Remove me"),
        SelectorCheck("name_attr", "name"),
    ]
    result = _CHECKER.check_fixture("broker", "page.html", checks, tmp_path)
    assert result.all_passed is True
    assert result.broker_slug == "broker"


def test_check_fixture_absent_required_selector(tmp_path):
    _write_fixture(tmp_path, "broker", "page.html", _FIXTURE_HTML)
    checks = [
        SelectorCheck("text", "Nonexistent button text", required=True),
    ]
    result = _CHECKER.check_fixture("broker", "page.html", checks, tmp_path)
    assert result.all_passed is False


def test_check_fixture_missing_file(tmp_path):
    checks = [SelectorCheck("text", "Remove me")]
    result = _CHECKER.check_fixture("no-broker", "page.html", checks, tmp_path)
    assert result.all_passed is False
    assert all(not passed for _, passed in result.checks)


def test_check_selector_text():
    html = "<p>Click Remove me here</p>"
    assert _CHECKER._check_selector(html, SelectorCheck("text", "Remove me")) is True
    assert _CHECKER._check_selector(html, SelectorCheck("text", "Nonexistent")) is False


def test_check_selector_id():
    html = '<input id="search-field" />'
    assert _CHECKER._check_selector(html, SelectorCheck("id", "search-field")) is True
    assert _CHECKER._check_selector(html, SelectorCheck("id", "missing-id")) is False


def test_check_selector_class():
    html = '<a class="optout-link">Remove</a>'
    assert _CHECKER._check_selector(html, SelectorCheck("class", "optout-link")) is True
    assert _CHECKER._check_selector(html, SelectorCheck("class", "missing-class")) is False


def test_check_selector_class_no_false_positive():
    """'link' must not match 'class="optout-link"' (substring false positive guard)."""
    html = '<a class="optout-link">Remove</a>'
    assert _CHECKER._check_selector(html, SelectorCheck("class", "link")) is False
    assert _CHECKER._check_selector(html, SelectorCheck("class", "optout")) is False
    # Full value match should work
    assert _CHECKER._check_selector(html, SelectorCheck("class", "optout-link")) is True


def test_check_selector_class_middle_token():
    """Middle token in multi-class attribute must be found."""
    html = '<div class="foo bar baz">x</div>'
    assert _CHECKER._check_selector(html, SelectorCheck("class", "bar")) is True
    assert _CHECKER._check_selector(html, SelectorCheck("class", "foo")) is True  # first
    assert _CHECKER._check_selector(html, SelectorCheck("class", "baz")) is True  # last


def test_check_selector_name_attr():
    html = '<input name="citystate" />'
    assert _CHECKER._check_selector(html, SelectorCheck("name_attr", "citystate")) is True
    assert _CHECKER._check_selector(html, SelectorCheck("name_attr", "missing")) is False


def test_optional_check_failure_does_not_affect_all_passed(tmp_path):
    _write_fixture(tmp_path, "broker", "page.html", _FIXTURE_HTML)
    checks = [
        SelectorCheck("text", "Remove me", required=True),
        SelectorCheck("text", "Nonexistent optional thing", required=False),
    ]
    result = _CHECKER.check_fixture("broker", "page.html", checks, tmp_path)
    assert result.all_passed is True  # required check passes; optional failure ignored


def test_all_optional_no_required_is_false(tmp_path):
    """No required checks → all_passed=False to avoid vacuous True."""
    _write_fixture(tmp_path, "broker", "page.html", _FIXTURE_HTML)
    checks = [
        SelectorCheck("text", "Nonexistent", required=False),
    ]
    result = _CHECKER.check_fixture("broker", "page.html", checks, tmp_path)
    assert result.all_passed is False


def test_required_absent_optional_present_is_false(tmp_path):
    """Required check absent + optional check present → all_passed=False."""
    _write_fixture(tmp_path, "broker", "page.html", _FIXTURE_HTML)
    checks = [
        SelectorCheck("text", "MISSING_REQUIRED_TEXT", required=True),
        SelectorCheck("text", "Remove me", required=False),
    ]
    result = _CHECKER.check_fixture("broker", "page.html", checks, tmp_path)
    assert result.all_passed is False


def test_generate_broker_status_passing(tmp_path):
    _write_fixture(tmp_path, "whitepages", "page.html", _FIXTURE_HTML)
    checks = [SelectorCheck("text", "Remove me")]
    result = _CHECKER.check_fixture("whitepages", "page.html", checks, tmp_path)
    statuses = generate_broker_status({"whitepages": result}, ["whitepages"])
    assert statuses[0].fixture_selectors_ok is True


def test_generate_broker_status_no_fixture():
    statuses = generate_broker_status({}, ["unknown-broker"])
    assert statuses[0].fixture_selectors_ok is None
    assert statuses[0].notes == "no fixture recorded"


def test_write_broker_status_valid_json(tmp_path):
    statuses = [BrokerStatus(broker_slug="test", fixture_selectors_ok=True)]
    output = tmp_path / "broker_status.json"
    write_broker_status(statuses, output)
    assert output.exists()
    data = json.loads(output.read_text())
    assert isinstance(data, list)
    assert data[0]["broker_slug"] == "test"


def test_broker_status_honest_language(tmp_path):
    """Status JSON must not use removed/deleted/verified language."""
    statuses = [
        BrokerStatus(broker_slug="a", fixture_selectors_ok=True,
                     notes="fixture check only — not a live verification"),
        BrokerStatus(broker_slug="b", fixture_selectors_ok=None,
                     notes="no fixture recorded"),
    ]
    output = tmp_path / "broker_status.json"
    write_broker_status(statuses, output)
    content = output.read_text()
    assert "removed" not in content.lower()
    assert "deleted" not in content.lower()
    assert "verified removal" not in content.lower()


def test_cli_validate_health_exits_zero(tmp_path):
    result = CliRunner().invoke(main, ["validate-health", "--output", str(tmp_path / "out.json")])
    assert result.exit_code == 0
    assert "Health check" in result.output
