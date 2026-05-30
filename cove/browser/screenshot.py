from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path


def save_screenshot(page, output_dir: Path, label: str = "error") -> Path:
    """Save a screenshot with a safe timestamp filename. Never uses PII in path.

    The label is sanitized: only lowercase alphanumerics, hyphens, and underscores
    are kept. Path separators and special chars are replaced with underscores.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = re.sub(r"[^a-z0-9_-]", "_", label.lower())
    filename = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f") + f"_{safe_label}.png"
    path = output_dir / filename
    page.screenshot(path=str(path))
    return path
