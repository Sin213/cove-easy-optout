from cove import updater


def test_version_newer():
    assert updater.version_newer("0.2.0", "0.1.9")
    assert updater.version_newer("v1.0.0", "0.9")
    assert not updater.version_newer("0.1.1", "0.1.1")
    assert not updater.version_newer("0.1.0-rc1", "0.1.0")


def test_env_var_disables_network_call(monkeypatch):
    calls = []
    monkeypatch.setattr(updater, "fetch_latest_release", lambda *a, **k: calls.append(1))
    monkeypatch.setenv("COVE_NO_UPDATE_CHECK", "1")
    updater.maybe_notify_update("0.1.0")
    assert calls == []


def test_notifies_when_newer_release(monkeypatch, capsys):
    monkeypatch.delenv("COVE_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(
        updater, "fetch_latest_release",
        lambda *a, **k: {"tag_name": "v9.9.9", "html_url": "https://example.invalid/r"},
    )
    updater.maybe_notify_update("0.1.0")
    assert "v9.9.9 is available" in capsys.readouterr().err


def test_silent_when_fetch_fails(monkeypatch, capsys):
    monkeypatch.delenv("COVE_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(updater, "fetch_latest_release", lambda *a, **k: None)
    updater.maybe_notify_update("0.1.0")
    assert capsys.readouterr().err == ""
