"""Update check backed by the GitHub releases API.

CLI variant of the Cove fleet updater: no GUI, no self-swap. When a newer
release exists, a one-line notice with the release URL is printed to
stderr. Failures (network, rate limit, no releases yet) are silent - an
update hint must never break or slow a working command.

When this repo starts shipping frozen artifacts (AppImage etc.), port the
full UpdateController from cove-pdf-editor (sha256-verified download and
versioned-filename AppImage swap) instead of extending this module.
"""
from __future__ import annotations

import json
import sys
import urllib.request

GITHUB_REPO = "Sin213/cove-easy-optout"


def _parse_version(v: str) -> tuple[int, int, int]:
    v = v.strip().lstrip("vV")
    out: list[int] = []
    for part in v.split("."):
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        out.append(int(digits) if digits else 0)
        if len(out) == 3:
            break
    while len(out) < 3:
        out.append(0)
    return (out[0], out[1], out[2])


def version_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def fetch_latest_release(repo: str = GITHUB_REPO, timeout: float = 4.0) -> dict | None:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{repo.split('/')[-1]}-updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except Exception:  # noqa: BLE001
        return None


def maybe_notify_update(current_version: str) -> None:
    """Print a one-line stderr notice if a newer release is published."""
    data = fetch_latest_release()
    if data is None:
        return
    tag = data.get("tag_name") or ""
    latest = tag.lstrip("vV")
    if not latest or not version_newer(latest, current_version):
        return
    url = (
        data.get("html_url")
        or f"https://github.com/{GITHUB_REPO}/releases/latest"
    )
    print(
        f"cove-easy-optout v{latest} is available "
        f"(you have v{current_version}): {url}",
        file=sys.stderr,
    )
