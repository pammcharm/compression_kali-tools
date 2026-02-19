from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PBKDF2_ITERATIONS = 200_000


@dataclass(slots=True)
class KeyMaterial:
    enc_key: bytes
    hmac_key: bytes
    salt: bytes


def derive_keys(password: str, salt: bytes | None = None) -> KeyMaterial:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=64
    )
    return KeyMaterial(enc_key=dk[:32], hmac_key=dk[32:], salt=salt)


def encrypt_block(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, plaintext, None)
    return nonce, ciphertext


def decrypt_block(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, None)


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()
