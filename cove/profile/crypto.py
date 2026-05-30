"""
Cryptographic primitives for the profile store.

Known limitation: Python str/bytes objects are immutable and may persist in
memory until GC. DEK and KEK cannot be reliably zeroed after use. This is an
accepted limitation of the CPython runtime for this local-MVP threat model.

No log statements in this module — key material and profile data must never
appear in log output.
"""
from __future__ import annotations

import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class DecryptionError(Exception):
    """Raised on authentication failure (wrong passphrase or tampered data)."""


_PBKDF2_ITERATIONS = 600_000
_KEY_LEN = 32  # 256-bit
_IV_LEN = 12   # 96-bit — standard for AES-GCM


def generate_salt() -> bytes:
    return os.urandom(16)


def generate_dek() -> bytes:
    return os.urandom(_KEY_LEN)


def derive_kek(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode(),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_KEY_LEN,
    )


def encrypt_with_kek(kek: bytes, dek: bytes) -> tuple[bytes, bytes]:
    """Encrypt DEK with KEK using AES-GCM. Returns (iv, ciphertext_with_tag)."""
    iv = os.urandom(_IV_LEN)
    ciphertext = AESGCM(kek).encrypt(iv, dek, None)
    return iv, ciphertext


def decrypt_with_kek(kek: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """Decrypt DEK. Raises DecryptionError on authentication failure."""
    try:
        return AESGCM(kek).decrypt(iv, ciphertext, None)
    except InvalidTag as exc:
        raise DecryptionError("DEK decryption failed: wrong passphrase or tampered data") from exc


def encrypt_data(dek: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """Encrypt profile bytes with DEK using AES-GCM. Returns (iv, ciphertext_with_tag)."""
    iv = os.urandom(_IV_LEN)
    ciphertext = AESGCM(dek).encrypt(iv, plaintext, None)
    return iv, ciphertext


def decrypt_data(dek: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """Decrypt profile bytes. Raises DecryptionError on authentication failure."""
    try:
        return AESGCM(dek).decrypt(iv, ciphertext, None)
    except InvalidTag as exc:
        raise DecryptionError("Data decryption failed: wrong passphrase or tampered data") from exc
