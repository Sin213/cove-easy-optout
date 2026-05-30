import json

import pytest

from cove.adapter import OptOutResult, OptOutStatus
from cove.report import BrokerReportRow, ReportWriter, RunReport, build_report

_RESULTS = [
    OptOutResult(broker_slug="whitepages", status=OptOutStatus.submitted, timestamp="2026-01-01T00:00:00Z"),
    OptOutResult(broker_slug="spokeo", status=OptOutStatus.manual_required, timestamp="2026-01-01T00:00:01Z", manual_url="https://spokeo.com/optout"),
    OptOutResult(broker_slug="intelius", status=OptOutStatus.failed, timestamp="2026-01-01T00:00:02Z"),
]


def test_build_report_counts():
    report = build_report(_RESULTS)
    assert report.total == 3
    assert report.submitted == 1
    assert report.manual_required == 1
    assert report.failed == 1
    assert report.awaiting_confirmation == 0
    assert report.profile_not_visible_as_of_date == 0


def test_build_report_all_status_types():
    results = [
        OptOutResult(broker_slug="a", status=OptOutStatus.submitted, timestamp="2026-01-01T00:00:00Z"),
        OptOutResult(broker_slug="b", status=OptOutStatus.awaiting_confirmation, timestamp="2026-01-01T00:00:01Z"),
        OptOutResult(broker_slug="c", status=OptOutStatus.manual_required, timestamp="2026-01-01T00:00:02Z"),
        OptOutResult(broker_slug="d", status=OptOutStatus.failed, timestamp="2026-01-01T00:00:03Z"),
        OptOutResult(broker_slug="e", status=OptOutStatus.profile_not_visible_as_of_date, timestamp="2026-01-01T00:00:04Z"),
    ]
    report = build_report(results)
    statuses = {row.status: row.next_action for row in report.rows}
    assert "inbox" in statuses["awaiting_confirmation"].lower()
    assert "manually" in statuses["manual_required"].lower()
    assert "retry" in statuses["failed"].lower()
    assert "no profile" in statuses["profile_not_visible_as_of_date"].lower()
    assert "await" in statuses["submitted"].lower()
    assert report.awaiting_confirmation == 1
    assert report.profile_not_visible_as_of_date == 1
    assert (report.submitted + report.awaiting_confirmation + report.manual_required
            + report.failed + report.profile_not_visible_as_of_date) == report.total


def test_build_report_manual_url_propagated():
    report = build_report(_RESULTS)
    spokeo_row = next(r for r in report.rows if r.broker_slug == "spokeo")
    assert spokeo_row.manual_url == "https://spokeo.com/optout"


def test_write_json_creates_file(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_json(report)
    assert path.exists()
    assert path.suffix == ".json"
    data = json.loads(path.read_text())
    assert data["total"] == 3
    assert "rows" in data
    assert len(data["rows"]) == 3


def test_write_json_structure(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_json(report)
    data = json.loads(path.read_text())
    row = data["rows"][0]
    assert "broker_slug" in row
    assert "status" in row
    assert "next_action" in row
    assert "timestamp" in row


def test_write_json_no_pii(tmp_path):
    results = [
        OptOutResult(
            broker_slug="test",
            status=OptOutStatus.submitted,
            timestamp="2026-01-01T00:00:00Z",
            message="Opt-out submitted",
        )
    ]
    report = build_report(results)
    writer = ReportWriter(tmp_path)
    path = writer.write_json(report)
    content = path.read_text()
    assert "Test User" not in content
    assert "test@example.com" not in content
    assert "555-867-5309" not in content


def test_write_html_creates_file(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    assert path.exists()
    assert path.suffix == ".html"


def test_write_html_contains_broker_slugs(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert "whitepages" in content
    assert "spokeo" in content
    assert "intelius" in content


def test_write_html_contains_status_values(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert "submitted" in content
    assert "manual_required" in content
    assert "failed" in content


def test_write_html_contains_disclaimer(tmp_path):
    report = build_report(_RESULTS)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert "Results do not confirm removal" in content
    assert "Verify directly with each broker" in content


def test_write_html_no_pii(tmp_path):
    results = [
        OptOutResult(broker_slug="test", status=OptOutStatus.submitted, timestamp="2026-01-01T00:00:00Z")
    ]
    report = build_report(results)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert "Test User" not in content
    assert "test@example.com" not in content
    assert "555-867-5309" not in content


def test_write_html_blocks_javascript_uri_in_manual_url(tmp_path):
    """javascript: URIs must not render as clickable links in HTML output."""
    results = [
        OptOutResult(
            broker_slug="test",
            status=OptOutStatus.manual_required,
            timestamp="2026-01-01T00:00:00Z",
            manual_url="javascript:alert(1)",
        )
    ]
    report = build_report(results)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert 'href="javascript:' not in content
    assert "<a " not in content  # no link rendered for javascript: URL


def test_write_html_omits_message_field(tmp_path):
    """message is internal — must not appear in HTML output."""
    results = [
        OptOutResult(
            broker_slug="test",
            status=OptOutStatus.submitted,
            timestamp="2026-01-01T00:00:00Z",
            message="internal-adapter-note-xyz",
        )
    ]
    report = build_report(results)
    writer = ReportWriter(tmp_path)
    path = writer.write_html(report)
    content = path.read_text()
    assert "internal-adapter-note-xyz" not in content
