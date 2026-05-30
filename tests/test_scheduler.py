from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cove.scheduler import (
    DEFAULT_RESCAN_DAYS,
    ScheduleStore,
    due_brokers,
)

_NOW = datetime(2026, 5, 30, 12, 0, 0, tzinfo=UTC)
_YESTERDAY = _NOW - timedelta(days=1)
_TOMORROW = _NOW + timedelta(days=1)


def _store(tmp_path: Path) -> ScheduleStore:
    return ScheduleStore(tmp_path / "schedule.json")


def test_record_run_creates_record(tmp_path):
    store = _store(tmp_path)
    rec = store.record_run("whitepages", "submitted")
    assert rec.broker_slug == "whitepages"
    assert rec.last_status == "submitted"
    assert rec.last_run_at.endswith("Z")
    assert rec.next_due_at.endswith("Z")


def test_record_run_submitted_uses_half_interval(tmp_path):
    store = _store(tmp_path)
    rec = store.record_run("whitepages", "submitted", rescan_days=30)
    run_dt = datetime.fromisoformat(rec.last_run_at.replace("Z", "+00:00"))
    due_dt = datetime.fromisoformat(rec.next_due_at.replace("Z", "+00:00"))
    delta = due_dt - run_dt
    assert abs(delta.total_seconds() - 15 * 86400) < 2  # 15 days ± 2s


def test_record_run_awaiting_confirmation_uses_half_interval(tmp_path):
    store = _store(tmp_path)
    rec = store.record_run("spokeo", "awaiting_confirmation", rescan_days=30)
    run_dt = datetime.fromisoformat(rec.last_run_at.replace("Z", "+00:00"))
    due_dt = datetime.fromisoformat(rec.next_due_at.replace("Z", "+00:00"))
    delta = due_dt - run_dt
    assert abs(delta.total_seconds() - 15 * 86400) < 2


def test_record_run_failed_uses_full_interval(tmp_path):
    store = _store(tmp_path)
    rec = store.record_run("intelius", "failed", rescan_days=60)
    run_dt = datetime.fromisoformat(rec.last_run_at.replace("Z", "+00:00"))
    due_dt = datetime.fromisoformat(rec.next_due_at.replace("Z", "+00:00"))
    delta = due_dt - run_dt
    assert abs(delta.total_seconds() - 60 * 86400) < 2


def test_record_run_custom_rescan_days(tmp_path):
    store = _store(tmp_path)
    rec = store.record_run("whitepages", "profile_not_visible_as_of_date", rescan_days=45)
    run_dt = datetime.fromisoformat(rec.last_run_at.replace("Z", "+00:00"))
    due_dt = datetime.fromisoformat(rec.next_due_at.replace("Z", "+00:00"))
    delta = due_dt - run_dt
    assert abs(delta.total_seconds() - 45 * 86400) < 2


def test_record_run_overwrites_existing(tmp_path):
    store = _store(tmp_path)
    store.record_run("whitepages", "submitted")
    store.record_run("whitepages", "failed")
    records = store.load()
    assert records["whitepages"].last_status == "failed"
    assert len(records) == 1


def test_load_empty_when_absent(tmp_path):
    store = _store(tmp_path)
    assert store.load() == {}


def test_load_round_trips_after_save(tmp_path):
    store = _store(tmp_path)
    store.record_run("whitepages", "submitted")
    store.record_run("spokeo", "failed")
    loaded = store.load()
    assert set(loaded.keys()) == {"whitepages", "spokeo"}
    assert loaded["whitepages"].last_status == "submitted"
    assert loaded["spokeo"].last_status == "failed"


def test_due_brokers_never_scanned_first(tmp_path):
    store = _store(tmp_path)
    store.record_run("whitepages", "submitted")
    records = store.load()
    result = due_brokers(records, ["whitepages", "new-broker"], as_of=_NOW)
    assert result[0] == "new-broker"


def test_due_brokers_overdue_sorted_most_overdue_first(tmp_path):
    from cove.scheduler import ScanRecord
    records = {
        "a": ScanRecord("a", "2026-01-01T00:00:00Z", "failed", "2026-01-10T00:00:00Z"),
        "b": ScanRecord("b", "2026-01-01T00:00:00Z", "failed", "2026-01-05T00:00:00Z"),
    }
    result = due_brokers(records, ["a", "b"], as_of=_NOW)
    # "b" is more overdue (due Jan 5 vs Jan 10)
    assert result == ["b", "a"]


def test_due_brokers_excludes_not_yet_due(tmp_path):
    from cove.scheduler import ScanRecord
    future = (_NOW + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    records = {
        "whitepages": ScanRecord("whitepages", "2026-01-01T00:00:00Z", "submitted", future),
    }
    result = due_brokers(records, ["whitepages"], as_of=_NOW)
    assert result == []


def test_due_brokers_registry_scoped(tmp_path):
    from cove.scheduler import ScanRecord
    past = "2026-01-01T00:00:00Z"
    records = {
        "whitepages": ScanRecord("whitepages", past, "failed", past),
        "not-in-registry": ScanRecord("not-in-registry", past, "failed", past),
    }
    result = due_brokers(records, ["whitepages"], as_of=_NOW)
    assert "not-in-registry" not in result
    assert "whitepages" in result
