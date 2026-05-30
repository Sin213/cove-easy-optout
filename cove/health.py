"""
Canary/fixture adapter health checker.

Checks adapter selectors against recorded HTML fixture snapshots to detect
selector rot — without live network calls and without real PII.

Known limitation: fixture checks use substring/attribute matching on raw HTML.
Playwright locators (get_by_label, get_by_role, get_by_text) use the live DOM.
Label-text rot may not be caught by fixtures unless fixture checks explicitly
include 'text' checks for the key label/button text the adapter targets.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "adapters" / "tests" / "fixtures"


@dataclass
class SelectorCheck:
    selector_type: str  # "text" | "id" | "class" | "name_attr"
    value: str
    required: bool = True


@dataclass
class HealthResult:
    broker_slug: str
    fixture_name: str
    checks: list[tuple[SelectorCheck, bool]]
    all_passed: bool
    checked_at: str


@dataclass
class BrokerStatus:
    broker_slug: str
    fixture_selectors_ok: bool | None = None   # None = no fixtures recorded
    last_fixture_check: str | None = None
    live_status: str | None = None             # null until explicit live canary run
    notes: str = ""


class AdapterHealthChecker:
    """Check adapter selectors against recorded HTML fixture files.

    Uses plain-text substring/attribute matching on raw HTML content.
    """

    def check_fixture(
        self,
        broker_slug: str,
        fixture_name: str,
        checks: list[SelectorCheck],
        fixtures_dir: Path = FIXTURES_DIR,
    ) -> HealthResult:
        fixture_path = fixtures_dir / broker_slug / fixture_name
        if not fixture_path.exists():
            return HealthResult(
                broker_slug=broker_slug,
                fixture_name=fixture_name,
                checks=[(c, False) for c in checks],
                all_passed=False,
                checked_at=_now_str(),
            )
        html = fixture_path.read_text(encoding="utf-8", errors="replace")
        results = [(check, self._check_selector(html, check)) for check in checks]
        required_results = [(c, p) for c, p in results if c.required]
        # all_passed=False when no required checks defined (avoid vacuous True on all-optional sets)
        all_passed = bool(required_results) and all(p for _, p in required_results)
        return HealthResult(
            broker_slug=broker_slug,
            fixture_name=fixture_name,
            checks=results,
            all_passed=all_passed,
            checked_at=_now_str(),
        )

    def _check_selector(self, html: str, check: SelectorCheck) -> bool:
        if check.selector_type == "text":
            return check.value.lower() in html.lower()
        if check.selector_type == "id":
            return (
                f'id="{check.value}"' in html
                or f"id='{check.value}'" in html
            )
        if check.selector_type == "class":
            # Check exact class value or as one token in a multi-class attribute.
            # No bare substring fallback — avoids false positives on partial matches.
            return (
                f'class="{check.value}"' in html
                or f"class='{check.value}'" in html
                or f'"{check.value} ' in html      # start of multi-class: "foo bar"
                or f' {check.value}"' in html       # end of multi-class: "bar baz"
                or f"'{check.value} " in html
                or f" {check.value}'" in html
                or f" {check.value} " in html       # middle token: "foo bar baz"
            )
        if check.selector_type == "name_attr":
            return (
                f'name="{check.value}"' in html
                or f"name='{check.value}'" in html
            )
        return False


def generate_broker_status(
    results: dict[str, HealthResult],
    all_slugs: list[str],
) -> list[BrokerStatus]:
    """Generate BrokerStatus list for broker_status.json output.

    Plain-text vs Playwright note: fixture checks detect attribute/text presence
    in raw HTML. Playwright locators may fail in ways fixtures cannot catch
    (e.g. label-text changes). Include 'text' checks for key label/button text
    to cover the most common Playwright locator rot.
    """
    statuses = []
    for slug in sorted(all_slugs):
        result = results.get(slug)
        if result:
            statuses.append(BrokerStatus(
                broker_slug=slug,
                fixture_selectors_ok=result.all_passed,
                last_fixture_check=result.checked_at,
                live_status=None,
                notes=(
                    "fixture check only — not a live verification; "
                    "label-text rot may not be caught (see cove/health.py)"
                ),
            ))
        else:
            statuses.append(BrokerStatus(
                broker_slug=slug,
                fixture_selectors_ok=None,
                last_fixture_check=None,
                live_status=None,
                notes="no fixture recorded",
            ))
    return statuses


def write_broker_status(statuses: list[BrokerStatus], output_path: Path) -> None:
    """Write broker_status.json. Does not overclaim coverage."""
    output_path.write_text(
        json.dumps(
            [
                {
                    "broker_slug": s.broker_slug,
                    "fixture_selectors_ok": s.fixture_selectors_ok,
                    "last_fixture_check": s.last_fixture_check,
                    "live_status": s.live_status,
                    "notes": s.notes,
                }
                for s in statuses
            ],
            indent=2,
        )
    )


def _now_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
