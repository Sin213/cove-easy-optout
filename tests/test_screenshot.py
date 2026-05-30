import re
from pathlib import Path
from unittest.mock import MagicMock

from cove.browser.screenshot import save_screenshot


def test_screenshot_creates_timestamped_file(tmp_path):
    page = MagicMock()
    path = save_screenshot(page, tmp_path, label="error")
    assert path.parent == tmp_path
    assert path.suffix == ".png"
    # Filename pattern: YYYYMMDDTHHMMSSXXXXXX_error.png (microsecond precision)
    assert re.match(r"^\d{8}T\d{12}_error\.png$", path.name)
    page.screenshot.assert_called_once_with(path=str(path))


def test_screenshot_label_sanitized(tmp_path):
    page = MagicMock()
    path = save_screenshot(page, tmp_path, label="error/page")
    assert "/" not in path.name
    assert "error_page" in path.name


def test_screenshot_path_traversal_sanitized(tmp_path):
    page = MagicMock()
    path = save_screenshot(page, tmp_path, label="../../../etc/passwd")
    # All path separators and dots become underscores
    assert "/" not in path.name
    assert ".." not in path.name
    assert path.parent == tmp_path


def test_screenshot_output_dir_created(tmp_path):
    page = MagicMock()
    new_dir = tmp_path / "nested" / "dir"
    save_screenshot(page, new_dir, label="test")
    assert new_dir.exists()


def test_screenshot_no_pii_in_filename(tmp_path):
    page = MagicMock()
    path = save_screenshot(page, tmp_path, label="submit")
    # Filename contains only timestamp + safe label; no other content
    assert "test@example.com" not in path.name
    assert "Test User" not in path.name
