"""
Profile store: saves and loads an encrypted Profile to a local file.

Log statements in this module must never include profile field values
(names, emails, phones, addresses, date_of_birth). Only operational
events ("profile saved", "profile loaded") may be logged.
"""
from __future__ import annotations

import json
import logging
import os
import stat
from pathlib import Path

from cove.profile.crypto import (
    DecryptionError,
    decrypt_data,
    decrypt_with_kek,
    derive_kek,
    encrypt_data,
    encrypt_with_kek,
    generate_dek,
    generate_salt,
)
from cove.profile.models import Profile

_STORE_VERSION = 1
_log = logging.getLogger(__name__)


class ProfileNotFoundError(Exception):
    """Raised when the profile file does not exist."""


class ProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def exists(self) -> bool:
        return self._path.exists()

    def save(self, profile: Profile, passphrase: str) -> None:
        """Encrypt and save profile. Generates fresh salt and IVs on every save."""
        plaintext = json.dumps(profile.to_dict()).encode()

        salt = generate_salt()
        kek = derive_kek(passphrase, salt)
        dek = generate_dek()

        kek_iv, encrypted_dek = encrypt_with_kek(kek, dek)
        data_iv, ciphertext = encrypt_data(dek, plaintext)

        payload = {
            "version": _STORE_VERSION,
            "salt": salt.hex(),
            "kek_iv": kek_iv.hex(),
            "encrypted_dek": encrypted_dek.hex(),
            "data_iv": data_iv.hex(),
            "ciphertext": ciphertext.hex(),
        }

        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload))
        os.replace(tmp, self._path)
        os.chmod(self._path, 0o600)

        _log.info("profile saved")

    def load(self, passphrase: str) -> Profile:
        """Decrypt and return Profile. Raises DecryptionError or ProfileNotFoundError."""
        if not self._path.exists():
            raise ProfileNotFoundError(f"No profile at {self._path}")

        payload = json.loads(self._path.read_text())

        salt = bytes.fromhex(payload["salt"])
        kek_iv = bytes.fromhex(payload["kek_iv"])
        encrypted_dek = bytes.fromhex(payload["encrypted_dek"])
        data_iv = bytes.fromhex(payload["data_iv"])
        ciphertext = bytes.fromhex(payload["ciphertext"])

        kek = derive_kek(passphrase, salt)
        dek = decrypt_with_kek(kek, kek_iv, encrypted_dek)
        plaintext = decrypt_data(dek, data_iv, ciphertext)

        _log.info("profile loaded")
        return Profile.from_dict(json.loads(plaintext))

    def update(self, profile: Profile, passphrase: str) -> None:
        self.save(profile, passphrase)

    def delete(self) -> None:
        if not self._path.exists():
            raise ProfileNotFoundError(f"No profile at {self._path}")
        self._path.unlink()
        _log.info("profile deleted")
