"""
Local rescan scheduler — data layer only, no background daemon.

Concurrency note: last-writer-wins. No file locking. This is a local single-user
tool invoked manually or by OS cron — concurrent writes are not an expected scenario.
If concurrent use is ever required, a proper lock file should be added then.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_RESCAN_DAYS = 30  # matches BrokerEntry.rescan_days default in the schema
ACTIVE_RESCAN_MULTIPLIER = 0.5  # submitted/awaiting_confirmation: half the interval

# Active statuses get a half-interval priority boost — the opt-out is still
# in-flight and the profile may still be live, so checking sooner makes sense.
# profile_not_visible_as_of_date and manual_required both use the full interval:
# - profile_not_visible_as_of_date: tentative success; re-list checks can wait
# - manual_required: terminal state for automation; user must act, not the scheduler
_ACTIVE_STATUSES = frozenset({"submitted", "awaiting_confirmation"})


@dataclass
class ScanRecord:
    broker_slug: str
    last_run_at: str    # ISO UTC
    last_status: str    # OptOutStatus value (stored as string for forward-compat)
    next_due_at: str    # ISO UTC — computed at record_run() time


def _now_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def _parse_dt(iso: str) -> datetime:
    # datetime.fromisoformat() does not accept "Z" suffix on Python < 3.11.
    # Normalise by replacing "Z" with "+00:00" before parsing.
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


class ScheduleStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> dict[str, ScanRecord]:
        """Return {slug: ScanRecord}. Empty dict if file absent."""
        if not self._path.exists():
            return {}
        data = json.loads(self._path.read_text())
        return {slug: ScanRecord(**rec) for slug, rec in data.items()}

    def save(self, records: dict[str, ScanRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({slug: asdict(rec) for slug, rec in records.items()}, indent=2)
        )

    def record_run(
        self,
        broker_slug: str,
        status: str,
        rescan_days: int = DEFAULT_RESCAN_DAYS,
    ) -> ScanRecord:
        """Record a completed run and compute next_due_at. Overwrites existing record."""
        records = self.load()
        now = datetime.now(UTC)
        interval_days = (
            rescan_days * ACTIVE_RESCAN_MULTIPLIER
            if status in _ACTIVE_STATUSES
            else float(rescan_days)
        )
        next_due = now + timedelta(days=interval_days)
        record = ScanRecord(
            broker_slug=broker_slug,
            last_run_at=now.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
            last_status=status,
            next_due_at=next_due.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
        )
        records[broker_slug] = record
        self.save(records)
        return record


def due_brokers(
    records: dict[str, ScanRecord],
    all_slugs: list[str],
    as_of: datetime | None = None,
) -> list[str]:
    """Return slugs that are due for re-scan, ordered by priority.

    Priority order:
    1. Never-scanned brokers (always due)
    2. Overdue brokers sorted by most-overdue first (earliest next_due_at first)
    """
    now = as_of or datetime.now(UTC)
    never_scanned = [s for s in all_slugs if s not in records]
    overdue = [
        (slug, rec)
        for slug, rec in records.items()
        if slug in all_slugs and _parse_dt(rec.next_due_at) <= now
    ]
    overdue.sort(key=lambda x: _parse_dt(x[1].next_due_at))
    return never_scanned + [slug for slug, _ in overdue]
