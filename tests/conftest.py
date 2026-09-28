import pytest


@pytest.fixture(autouse=True)
def _no_update_check(monkeypatch):
    """Keep the suite offline: CLI commands would otherwise query GitHub releases."""
    monkeypatch.setenv("COVE_NO_UPDATE_CHECK", "1")
