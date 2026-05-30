import json
import logging
import os
import stat

import pytest

from cove.profile.crypto import DecryptionError
from cove.profile.models import Address, Profile
from cove.profile.store import ProfileNotFoundError, ProfileStore

_PASS = "test-passphrase-abc"

_PROFILE = Profile(
    names=["Test User"],
    emails=["test@example.com"],
    phones=["555-867-5309"],
    addresses=[Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")],
)


def test_save_load_round_trip(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    loaded = store.load(_PASS)
    assert loaded == _PROFILE


def test_wrong_passphrase_raises(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    with pytest.raises(DecryptionError):
        store.load("wrong-passphrase")


def test_stored_file_has_no_plaintext_pii(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    raw = (tmp_path / "profile.enc").read_bytes()
    assert b"Test User" not in raw
    assert b"test@example.com" not in raw
    assert b"555-867-5309" not in raw
    assert b"123 Main St" not in raw


def test_iv_salt_unique_across_saves(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    payload1 = json.loads((tmp_path / "profile.enc").read_text())
    store.save(_PROFILE, _PASS)
    payload2 = json.loads((tmp_path / "profile.enc").read_text())
    assert payload1["salt"] != payload2["salt"]
    assert payload1["kek_iv"] != payload2["kek_iv"]
    assert payload1["data_iv"] != payload2["data_iv"]


def test_file_permissions_are_restricted(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    mode = stat.S_IMODE(os.stat(tmp_path / "profile.enc").st_mode)
    assert mode == 0o600


def test_log_cleanliness(tmp_path, caplog):
    store = ProfileStore(tmp_path / "profile.enc")
    with caplog.at_level(logging.DEBUG):
        store.save(_PROFILE, _PASS)
        store.load(_PASS)
    for record in caplog.records:
        assert "Test User" not in record.message
        assert "test@example.com" not in record.message
        assert "555-867-5309" not in record.message
        assert "123 Main St" not in record.message


def test_delete_removes_file(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    assert store.exists()
    store.delete()
    assert not store.exists()


def test_double_delete_raises(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    store.save(_PROFILE, _PASS)
    store.delete()
    with pytest.raises(ProfileNotFoundError):
        store.delete()


def test_exists_lifecycle(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    assert not store.exists()
    store.save(_PROFILE, _PASS)
    assert store.exists()
    store.delete()
    assert not store.exists()


def test_load_missing_raises(tmp_path):
    store = ProfileStore(tmp_path / "profile.enc")
    with pytest.raises(ProfileNotFoundError):
        store.load(_PASS)
