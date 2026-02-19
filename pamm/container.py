from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from typing import Any

MAGIC = b"PAMM01"
VERSION = 1
MODE_FAST = 0
MODE_FULL = 1
FLAG_ENCRYPTED = 0x01
FOOTER_MAGIC = b"FTR1"

HEADER_STRUCT = struct.Struct("<6sBBHBBHQQ")


@dataclass(slots=True)
class ContainerEnvelope:
    mode: int
    encrypted: bool
    salt: bytes
    metadata: dict[str, Any]
    payload: bytes
    sha256: bytes
    hmac_sha256: bytes


def pack_container(
    *,
    mode: int,
    encrypted: bool,
    salt: bytes,
    metadata: dict[str, Any],
    payload: bytes,
    hmac_value: bytes | None,
) -> bytes:
    metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    flags = FLAG_ENCRYPTED if encrypted else 0
    header = HEADER_STRUCT.pack(
        MAGIC,
        VERSION,
        mode,
        flags,
        len(salt),
        0,
        0,
        len(metadata_bytes),
        len(payload),
    )
    body = header + salt + metadata_bytes + payload
    sha = hashlib.sha256(body).digest()
    footer = FOOTER_MAGIC + sha + (hmac_value if hmac_value else (b"\x00" * 32))
    return body + footer


def unpack_container(blob: bytes) -> ContainerEnvelope:
    min_size = HEADER_STRUCT.size + 4 + 32 + 32
    if len(blob) < min_size:
        raise ValueError("File too small to be a PAMM container")

    footer = blob[-68:]
    if footer[:4] != FOOTER_MAGIC:
        raise ValueError("Invalid PAMM footer")

    sha_expected = footer[4:36]
    hmac_expected = footer[36:68]
    body = blob[:-68]
    sha_actual = hashlib.sha256(body).digest()
    if sha_actual != sha_expected:
        raise ValueError("SHA-256 archive checksum mismatch")

    (
        magic,
        version,
        mode,
        flags,
        salt_len,
        _,
        _,
        metadata_len,
        payload_len,
    ) = HEADER_STRUCT.unpack_from(body, 0)

    if magic != MAGIC:
        raise ValueError("Invalid PAMM magic")
    if version != VERSION:
        raise ValueError(f"Unsupported PAMM version: {version}")

    start = HEADER_STRUCT.size
    salt = body[start : start + salt_len]
    start += salt_len
    metadata_bytes = body[start : start + metadata_len]
    start += metadata_len
    payload = body[start : start + payload_len]

    metadata = json.loads(metadata_bytes.decode("utf-8"))
    return ContainerEnvelope(
        mode=mode,
        encrypted=bool(flags & FLAG_ENCRYPTED),
        salt=salt,
        metadata=metadata,
        payload=payload,
        sha256=sha_expected,
        hmac_sha256=hmac_expected,
    )
