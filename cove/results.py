from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cove.adapter import OptOutResult, _now


class ResultStore:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir

    def save(self, results: list[OptOutResult]) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        run_at = _now()
        # Microsecond precision avoids filename collisions in rapid successive runs
        filename = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f") + "_run.json"
        path = self._dir / filename
        path.write_text(json.dumps({
            "run_at": run_at,
            "results": [r.to_dict() for r in results],
        }))
        return path

    def load_latest(self) -> list[OptOutResult]:
        runs = self.list_runs()
        if not runs:
            raise FileNotFoundError("No run results found in output directory")
        data = json.loads(runs[0].read_text())
        return [OptOutResult.from_dict(r) for r in data["results"]]

    def list_runs(self) -> list[Path]:
        if not self._dir.exists():
            return []
        return sorted(self._dir.glob("*_run.json"), reverse=True)
