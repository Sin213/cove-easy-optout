from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cove.adapter import OptOutResult, OptOutStatus

_NEXT_ACTION = {
    OptOutStatus.submitted: "Await broker confirmation. Re-scan in 30 days.",
    OptOutStatus.awaiting_confirmation: "Check your inbox and click the confirmation link.",
    OptOutStatus.manual_required: "Complete opt-out manually at the URL provided.",
    OptOutStatus.failed: "Retry this broker or complete manually.",
    OptOutStatus.profile_not_visible_as_of_date: "No profile found. Re-scan periodically.",
}


@dataclass
class BrokerReportRow:
    broker_slug: str
    status: str
    timestamp: str
    message: str      # internal only — omitted from HTML; JSON consumers must not display without PII review
    next_action: str
    manual_url: str = ""


@dataclass
class RunReport:
    generated_at: str
    total: int
    submitted: int
    awaiting_confirmation: int
    manual_required: int
    failed: int
    profile_not_visible_as_of_date: int
    rows: list[BrokerReportRow]


def build_report(results: list[OptOutResult]) -> RunReport:
    rows = [
        BrokerReportRow(
            broker_slug=r.broker_slug,
            status=r.status.value,
            timestamp=r.timestamp,
            message=r.message,
            next_action=_NEXT_ACTION.get(r.status, "Review status manually."),
            manual_url=r.manual_url,
        )
        for r in results
    ]
    return RunReport(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        total=len(results),
        submitted=sum(1 for r in results if r.status == OptOutStatus.submitted),
        awaiting_confirmation=sum(1 for r in results if r.status == OptOutStatus.awaiting_confirmation),
        manual_required=sum(1 for r in results if r.status == OptOutStatus.manual_required),
        failed=sum(1 for r in results if r.status == OptOutStatus.failed),
        profile_not_visible_as_of_date=sum(
            1 for r in results if r.status == OptOutStatus.profile_not_visible_as_of_date
        ),
        rows=rows,
    )


class ReportWriter:
    """Write JSON and HTML reports to an output directory."""

    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir

    def write_json(self, report: RunReport) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f") + "_report.json"
        path = self._dir / filename
        path.write_text(json.dumps(asdict(report), indent=2))
        return path

    def write_html(self, report: RunReport) -> Path:
        from jinja2 import Environment, FileSystemLoader
        self._dir.mkdir(parents=True, exist_ok=True)
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        tmpl = env.get_template("report.html.j2")
        html = tmpl.render(report=report)
        filename = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f") + "_report.html"
        path = self._dir / filename
        path.write_text(html)
        return path
