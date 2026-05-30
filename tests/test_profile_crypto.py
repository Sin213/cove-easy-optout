import pytest

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


def test_derive_kek_deterministic():
    salt = generate_salt()
    kek1 = derive_kek("passphrase", salt)
    kek2 = derive_kek("passphrase", salt)
    assert kek1 == kek2


def test_derive_kek_different_salts_differ():
    kek1 = derive_kek("passphrase", generate_salt())
    kek2 = derive_kek("passphrase", generate_salt())
    assert kek1 != kek2


def test_dek_round_trip():
    kek = derive_kek("test-pass", generate_salt())
    dek = generate_dek()
    iv, ct = encrypt_with_kek(kek, dek)
    assert decrypt_with_kek(kek, iv, ct) == dek


def test_data_round_trip():
    dek = generate_dek()
    plaintext = b"hello world profile data"
    iv, ct = encrypt_data(dek, plaintext)
    assert decrypt_data(dek, iv, ct) == plaintext


def test_wrong_passphrase_raises_decryption_error():
    salt = generate_salt()
    kek = derive_kek("correct-pass", salt)
    dek = generate_dek()
    iv, ct = encrypt_with_kek(kek, dek)

    wrong_kek = derive_kek("wrong-pass", salt)
    with pytest.raises(DecryptionError):
        decrypt_with_kek(wrong_kek, iv, ct)


def test_ciphertext_tamper_raises_decryption_error():
    dek = generate_dek()
    iv, ct = encrypt_data(dek, b"sensitive data")
    tampered = bytearray(ct)
    tampered[-1] ^= 0xFF  # flip last byte
    with pytest.raises(DecryptionError):
        decrypt_data(dek, iv, bytes(tampered))


def test_encrypted_dek_tamper_raises_decryption_error():
    kek = derive_kek("test-pass", generate_salt())
    dek = generate_dek()
    iv, ct = encrypt_with_kek(kek, dek)
    tampered = bytearray(ct)
    tampered[-1] ^= 0xFF
    with pytest.raises(DecryptionError):
        decrypt_with_kek(kek, iv, bytes(tampered))


def test_iv_length_is_12_bytes():
    dek = generate_dek()
    iv, _ = encrypt_data(dek, b"test")
    assert len(iv) == 12

    kek = derive_kek("pass", generate_salt())
    kek_iv, _ = encrypt_with_kek(kek, dek)
    assert len(kek_iv) == 12
