import pytest

from adapters.mock import MockAdapter
from cove.adapter import OptOutResult, OptOutStatus, _now
from cove.results import ResultStore


def _make_results() -> list[OptOutResult]:
    return [
        OptOutResult(broker_slug="a", status=OptOutStatus.submitted, timestamp=_now()),
        OptOutResult(broker_slug="b", status=OptOutStatus.manual_required, timestamp=_now(),
                     manual_url="https://example.com/b"),
    ]


def test_save_creates_file(tmp_path):
    store = ResultStore(tmp_path / "output")
    path = store.save(_make_results())
    assert path.exists()
    assert path.suffix == ".json"


def test_load_latest_round_trip(tmp_path):
    store = ResultStore(tmp_path / "output")
    original = _make_results()
    store.save(original)
    loaded = store.load_latest()
    assert len(loaded) == len(original)
    for orig, loaded_r in zip(original, loaded):
        assert orig.broker_slug == loaded_r.broker_slug
        assert orig.status == loaded_r.status
        assert orig.manual_url == loaded_r.manual_url


def test_list_runs_newest_first(tmp_path):
    store = ResultStore(tmp_path / "output")
    p1 = store.save(_make_results())
    p2 = store.save(_make_results())
    runs = store.list_runs()
    assert len(runs) == 2
    # Lexicographic sort on microsecond-precision names means newest is first
    assert runs[0].name >= runs[1].name


def test_load_latest_empty_raises(tmp_path):
    store = ResultStore(tmp_path / "empty")
    with pytest.raises(FileNotFoundError):
        store.load_latest()


def test_list_runs_missing_dir(tmp_path):
    store = ResultStore(tmp_path / "nonexistent")
    assert store.list_runs() == []
